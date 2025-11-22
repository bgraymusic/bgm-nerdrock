'''Commands that call through to the Nerdrock CDK app'''

import json
import pprint
import re
import time
import typing
import yaml

import boto3
import botocore.response
import botocore.exceptions
import mypy_boto3_cloudformation as boto3_cf
from mypy_boto3_cloudformation import type_defs as boto3_cf_types
import mypy_boto3_cloudfront as boto3_cfront
import mypy_boto3_lambda as boto3_lambda
import mypy_boto3_route53 as boto3_r53
import mypy_boto3_s3 as boto3_s3
import mypy_boto3_ssm as boto3_ssm

from cli import bgnr_command
from cli.bgnr_util import Config, Context, Out, Proc
from cli.commands.bgnr_local import PackageLambdasCommand, PackageWebCommand


class BootstrapCommand(bgnr_command.Command):
    '''Set up AWS account with the ability to deploy CDK infrastructure

    **USAGE**
      bgnr [flags] bootstrap

    {flags}

    **EXAMPLES**
      $ bgnr -v bootstrap
      $ bgnr bootstrap
    '''

    @classmethod
    def key(cls):
        return 'bootstrap'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(pip_features=['cdk'], prerequisites=[])

    def execute(self):
        cf_client: boto3_cf.CloudFormationClient = boto3.client('cloudformation')
        try:
            Out.trace('aws cloudformation describe-stacks --stack-name CDKToolkit')
            stack = cf_client.describe_stacks(StackName=Config.get().cdk_bootstrap_stack).get('Stacks')[0]
            output = next(
                (x for x in stack.get('Outputs') or [] if x and x.get('OutputKey') == 'BootstrapVersion'),
                None
            )
            if output and int(output.get('OutputValue') or -1) >= int(Config.get().min_bootstrap_ver):
                Out.target(Out.success('CDK already bootstrapped.'))
                bootstrap_msg = ''
                bootstrap_required = False
            else:
                bootstrap_msg = 'CDK bootstrap is old, updating'
                bootstrap_required = True
        except botocore.exceptions.ValidationError:
            bootstrap_msg = 'CDK not bootstrapped yet, bootstrapping'
            bootstrap_required = True

        if bootstrap_required:
            with Out.Do(msg=bootstrap_msg, error='Bootstrap failed!'):
                Proc.exec('cdk bootstrap')


class SynthCommand(bgnr_command.EnvCommand):
    '''Synthesize CloudFormation and output to the cdk.out directory

    **USAGE**
      bgnr [flags] synth [options]

    **OPTIONS**
      -e, --environment  The name of the environment to synthesize. This will
                         affect logical and physical IDs. Supplying 'prod' will
                         result in the production color being assigned that would
                         next be targeted by a production deployment.
                         [default == 'sandbox']

    {flags}

    **EXAMPLES**
      $ bgnr -c synth
      $ bgnr synth -e staging
      $ bgnr -c synth -e 'feature/guitar-tabs'
    '''

    @classmethod
    def key(cls):
        return 'synth'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(
            pip_features=['cdk'],
            prerequisites=[PackageWebCommand, PackageLambdasCommand, BootstrapCommand]
        )

    def execute(self):
        stack = f'{Config.get().org}-{Config.get().project}-{Context.get().environment}-stack'
        with Out.Do(msg=f'Synthesizing stack {stack}',
                    error='Synthesis failed, see above for details',
                    done='Synthesis complete; find template in cdk.out'):
            Proc.exec(f'cdk synth -c ENV={Context.get().environment}')


class DeployGlobalCommand(bgnr_command.Command):
    '''Deploy the global stack by itself, without an environment stack

    **USAGE**
      bgnr [flags] global

    {flags}

    **EXAMPLES**
      $ bgnr -v global
      $ bgnr global
    '''

    @classmethod
    def key(cls):
        return 'global'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(pip_features=['cdk'], prerequisites=[BootstrapCommand])

    def execute(self):
        with Out.Do(msg='Deploying global stack', error='Global deployment failed, see above for details'):
            Proc.exec('cdk deploy BgmNerdrockGlobalStack')
            Out.target(Out.success('Global deployment complete.'))


class DeployEnvCommand(bgnr_command.EnvCommand):
    '''Deploy project to the named environment or next production color (via -e prod)

    **USAGE**
      bgnr [flags] deploy [options]

    **OPTIONS**
      -e, --environment  The name of the environment to deploy. This will
                         affect logical and physical IDs. Supplying 'prod' will
                         result in the production color being assigned that would
                         next be targeted by a production deployment.
                         [default == 'sandbox']

    {flags}

    **EXAMPLES**
      $ bgnr -c deploy
      $ bgnr deploy -e staging
      $ bgnr -c deploy -e 'feature/guitar-tabs'
    '''

    @classmethod
    def key(cls):
        return 'deploy'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(
            pip_features=['cdk'],
            prerequisites=[PackageWebCommand, PackageLambdasCommand, BootstrapCommand]
        )

    def execute(self):
        msg = 'Deploying production stack' if Context.get().environment == 'prod' \
            else f'Deploying stack {Config.get().stack(Context.get().environment)}'
        with Out.Do(msg=msg, done='Deployment complete.', error='Deployment failed.  See above.'):
            verbose = Context.get().verbose
            Context.get().verbose = True  # Exception to the rule: always output deploy progress as it happens
            Proc.exec(f'cdk deploy --all -c ENV={Context.get().environment}', capture_stdout=True)
            Context.get().verbose = verbose
            with open('stacks.yml', 'r', encoding='utf-8') as f:
                stacks = yaml.load(f, yaml.Loader)
            if Context.get().verbose:
                print('Synthesized stacks: ', end='')
                print(pprint.pprint(stacks, indent=2))
            env_stack = stacks[-1]
            outputs = self.get_stack_outputs(env_stack)

        if env_stack:
            self.bootstrap_secrets()
            self.refresh_db(outputs)
            if Context.get().environment == 'prod':
                self.update_domain_records(env_stack)
                self.update_prod_color(env_stack)

    def get_stack_outputs(self, stack: str) -> list[boto3_cf_types.OutputTypeDef]:
        cf_client: boto3_cf.CloudFormationClient = boto3.client('cloudformation')
        return cf_client.describe_stacks(StackName=stack)['Stacks'][0].get('Outputs') or []

    def bootstrap_secrets(self):
        secrets_bucket = None
        secrets_file = None
        s3_client: boto3_s3.S3Client = boto3.client('s3')

        with Out.Do('Checking for global secrets file'):
            Out.trace(f'aws cloudformation describe-stacks --stack-name {Config.get().stack('global')}')
            outputs = self.get_stack_outputs(Config.get().stack('global'))
            secrets_bucket = next((x for x in outputs if x.get('OutputKey') == 'SecretsBucketName')).get('OutputValue')
            Out.trace(f'  -> secrets_bucket: {secrets_bucket}')
            if secrets_bucket:
                Out.trace(f'aws s3api list-objects --bucket {secrets_bucket}')
                contents = s3_client.list_objects_v2(Bucket=secrets_bucket).get('Contents') or []
                secrets_file = next((x.get('Key') for x in contents if x.get('Key') == 'secrets.yml'), None)
                Out.trace(f'  -> secrets_file: {secrets_file}')

        if not secrets_bucket:
            Out.target(f'{Out.failure('Secrets bucket not found!')}'
                       'Was BootstrapCommand.bootstrap_secrets somehow run before a successful global deployment?')
        elif not secrets_file:
            with Out.Do('Global secrets file is missing; uploading local secrets file'):
                Out.trace(f'aws s3 cp local/secrets.yml s3://{secrets_bucket}/')
                s3_client.upload_file(Filename='local/secrets.yml', Bucket=secrets_bucket, Key='secrets.yml')

    def refresh_db(self, outputs: list[boto3_cf_types.OutputTypeDef]):
        with Out.Do(msg='Finding the database refresh function',
                    error='Error getting database refresh function'):
            function_name = next((val for x in outputs if (
                (key := x.get('OutputKey')) is not None and
                'DatabaseLambdaName' in key and
                (val := x.get('OutputValue')) is not None
            )))

        with Out.Do(msg=f'Found function {function_name}, refreshing data from Bandcamp',
                    error=f'Error invoking lambda function {function_name}'):
            lambda_client: boto3_lambda.LambdaClient = boto3.client('lambda')
            Out.trace(f'aws lambda invoke --function-name {function_name} /dev/stdout')
            payload: botocore.response.StreamingBody = lambda_client.invoke(FunctionName=function_name)['Payload']
            response = json.load(payload)
            if Context.get().verbose:
                print(f'\n{json.dumps(response, indent=2)}')

    def update_domain_records(self, env_stack: str):
        with Out.Do(msg='Finding HostedZone to update', error='Error finding HostedZone'):
            cf_client: boto3_cf.CloudFormationClient = boto3.client('cloudformation')
            resources = cf_client.list_stack_resources(StackName=Config.get().stack('global'))['StackResourceSummaries']
            hosted_zone = next(hz for x in resources if (
                x.get('ResourceType') == 'AWS::Route53::HostedZone' and
                (hz := x.get('PhysicalResourceId')) is not None
            ))

        with Out.Do(msg='Finding the target distribution for prod DNS record update',
                    error='Error getting target distribution'):
            env_resources = cf_client.list_stack_resources(StackName=env_stack)['StackResourceSummaries']
            distribution_id = next(did for x in env_resources if (
                x.get('ResourceType') == 'AWS::CloudFront::Distribution' and
                (did := x.get('PhysicalResourceId')) is not None
            ))
            cfront_client: boto3_cfront.CloudFrontClient = boto3.client('cloudfront')
            distribution_domain = cfront_client.get_distribution(Id=distribution_id)['Distribution']['DomainName']

        with Out.Do(msg=f'Pointing {Config.get().domain} to the deployed prod distribution'):
            r53_client: boto3_r53.Route53Client = boto3.client('route53')
            for record_type in typing.Literal['A', 'AAAA'].__args__:
                r53_client.change_resource_record_sets(HostedZoneId=hosted_zone, ChangeBatch={
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': Config.get().domain,
                            'Type': record_type,
                            'AliasTarget': {
                                'HostedZoneId': Config.get().cf_hosted_zone,
                                'DNSName': distribution_domain,
                                'EvaluateTargetHealth': False
                            }
                        }
                    }]
                })
            r53_client.change_resource_record_sets(HostedZoneId=hosted_zone, ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': f'_.{Config.get().domain}.',
                        'Type': 'TXT',
                        'ResourceRecords': [{'Value': f'"{distribution_domain}."'}],
                        'TTL': 300
                    }
                }]
            })

        with Out.Do(msg=f'Moving alternate domain name for {Config.get().domain} to new distribution'):
            time.sleep(5)  # Takes a bit for the record to be seen, even if it shows back from an API call
            cfront_client.associate_alias(TargetDistributionId=distribution_id, Alias=Config.get().domain)

    def update_prod_color(self, env_stack: str):
        match: re.Match[str] | None = re.match(fr'{Config.get().org}-{Config.get().project}-(\w+?)-stack', env_stack)
        prod_color = match.groups()[0] if match else Config.get().default_prod_color
        with Out.Do(msg=f'Setting new active prod color to {prod_color}',
                    error=f'Error updating the prod color to {prod_color}; DNS and SSM are mismatched!'):
            Out.trace(f'aws ssm put-parameter --name bgm-nerdrock-active-prod-color --value {prod_color} --overwrite')
            ssm_client: boto3_ssm.SSMClient = boto3.client('ssm')
            ssm_client.put_parameter(Name='bgm-nerdrock-active-prod-color', Value=prod_color, Overwrite=True)


class UndeployCommand(bgnr_command.EnvCommand):
    '''Teardown named environment. In practice only used on branch deletion or local prototyping

    **USAGE**
      bgnr [flags] undeploy [options]

    **OPTIONS**
      -e, --environment  The name of the environment to tear down. Supplying 'prod' will
                         result in the production color being assigned that would
                         next be targeted by a production deployment.
                         [default == 'sandbox']

    {flags}

    **EXAMPLES**
      $ bgnr -c undeploy
      $ bgnr undeploy -e staging
      $ bgnr -c undeploy -e 'feature/guitar-tabs'
    '''

    @classmethod
    def key(cls):
        return 'undeploy'

    @classmethod
    def dependencies(cls) -> bgnr_command.Command.Dependencies:
        return bgnr_command.Command.Dependencies(
            pip_features=['cdk'],
            prerequisites=[PackageWebCommand, PackageLambdasCommand, BootstrapCommand]
        )

    def execute(self):
        if Context.get().environment == 'global':
            Out.failure('ATTEMPTING TO DELETE THE GLOBAL STACK!!! COMMAND REJECTED.')
        with Out.Do(msg=f'Deleting stack {Config.get().stack(Context.get().environment)}',
                    error=f'Failed to delete stack {Config.get().stack(Context.get().environment)}'):
            Proc.exec(f'cdk destroy -f -c ENV={Context.get().environment} '
                      f'{Config.get().to_logical(Config.get().stack(Context.get().environment))}')
