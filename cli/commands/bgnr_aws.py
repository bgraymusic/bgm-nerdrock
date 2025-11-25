'''Commands that use the AWS API via boto3'''

import time
import typing
import boto3
from mypy_boto3_cloudformation import client as boto3_cf
from mypy_boto3_cloudfront import client as boto3_cfront
from mypy_boto3_cloudfront_keyvaluestore import client as boto3_cfront_kvs
from mypy_boto3_route53 import client as boto3_r53
from mypy_boto3_ssm import client as boto3_ssm

from cli import bgnr_command
from cli import bgnr_util


class RollbackCommand(bgnr_command.Command):
    '''Rollback to previous deployment by repointing the DNS domain record

    **USAGE**
      bgnr [flags] rollback

    {flags}

    **EXAMPLES**
      $ bgnr rollback
      $ bgnr -v rollback
    '''

    @classmethod
    def key(cls):
        return 'rollback'

    def execute(self):
        ssm_client: boto3_ssm.SSMClient = boto3.client('ssm')

        with bgnr_util.Out.Do(msg='Fetching deployment color parameters'):
            response = ssm_client.get_parameters(Names=['bgm-nerdrock-prod-deployment-colors',
                                                        'bgm-nerdrock-active-prod-color'])
            active_color = next(val for x in response.get('Parameters') if (
                x.get('Name') == 'bgm-nerdrock-active-prod-color' and (val := x.get('Value')) is not None
            ))
            color_list: list[str] = next(val.split(',') for x in response.get('Parameters') if (
                x.get('Name') == 'bgm-nerdrock-prod-deployment-colors' and (val := x.get('Value')) is not None
            ))
            prev_color = color_list[-1] if (
                active_color == color_list[0]
             ) else (
                 color_list[color_list.index(active_color)-1]
             )

        with bgnr_util.Out.Do(msg='Finding HostedZone to update', error='Error finding HostedZone'):
            cf_client: boto3_cf.CloudFormationClient = boto3.client('cloudformation')
            global_resources = cf_client.list_stack_resources(
                StackName=bgnr_util.CliConfig.get().stack('global')
            )['StackResourceSummaries']
            hosted_zone = next(hz for x in global_resources if (
                x.get('ResourceType') == 'AWS::Route53::HostedZone' and (hz := x.get('PhysicalResourceId')) is not None
            ))

        with bgnr_util.Out.Do(msg='Finding the target distribution for prod DNS record update',
                    error='Error getting target distribution'):
            env_resources = cf_client.list_stack_resources(
                StackName=bgnr_util.CliConfig.get().stack(prev_color)
            )['StackResourceSummaries']
            distribution_id = next(prid for x in env_resources if (
                x.get('ResourceType') == 'AWS::CloudFront::Distribution' and
                (prid := x.get('PhysicalResourceId')) is not None
            ))
            cfront_client: boto3_cfront.CloudFrontClient = boto3.client('cloudfront')
            distribution_domain = cfront_client.get_distribution(Id=distribution_id)['Distribution']['DomainName']

        with bgnr_util.Out.Do(msg=f'Rolling back from {active_color} to {prev_color}',
                    error=f'Failed to roll back; prod is still pointed to {active_color}'):
            r53_client: boto3_r53.Route53Client = boto3.client('route53')
            for record_type in typing.Literal['A', 'AAAA'].__args__:
                r53_client.change_resource_record_sets(HostedZoneId=hosted_zone, ChangeBatch={
                    'Changes': [{
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': bgnr_util.CliConfig.get().domain,
                            'Type': record_type,
                            'AliasTarget': {
                                'HostedZoneId': bgnr_util.CliConfig.get().cf_hosted_zone,
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
                        'Name': f'_.{bgnr_util.CliConfig.get().domain}.',
                        'Type': 'TXT',
                        'ResourceRecords': [{'Value': f'"{distribution_domain}."'}],
                        'TTL': 300
                    }
                }]
            })

            time.sleep(5)  # Takes a bit for the record to be seen, even if it shows back from an API call
            cfront_client.associate_alias(TargetDistributionId=distribution_id, Alias=bgnr_util.CliConfig.get().domain)

        with bgnr_util.Out.Do(msg=f'Setting {prev_color} as the new active prod color',
                    error=f'Error updating the prod color to {prev_color}; DNS and SSM are mismatched!'):
            ssm_client.put_parameter(Name='bgm-nerdrock-active-prod-color', Value=prev_color, Overwrite=True)


class UpdateLocCommand(bgnr_command.Command):
    '''Update the IP address that non-prod environments will allow to connect

    **USAGE**
      bgnr [flags] update-loc

    {flags}

    **EXAMPLES**
      $ bgnr update-loc
      $ bgnr -v update-loc

    **NOTES**
      Non-prod environments have an IP-based protection that only allows
      access from one allowed source. That will usually be my home, but in
      case I'm on the road, I can execute this and it will update the allowed
      IP with wherever I happen to be.
    '''

    @classmethod
    def key(cls):
        return 'update-loc'

    def execute(self):
        with bgnr_util.Out.Do('Fetching public IP addresses'):
            ipv4 = bgnr_util.Proc.exec(bgnr_util.CliConfig.get().ipv4_check, capture_stdout=True).stdout.strip()
            ipv6 = bgnr_util.Proc.exec(bgnr_util.CliConfig.get().ipv6_check, capture_stdout=True).stdout.strip()
        with bgnr_util.Out.Do(f'Updating key-value store with current location {ipv4}/{ipv6}'):
            cf_client: boto3_cf.CloudFormationClient = boto3.client('cloudformation')
            stack_name = f'{bgnr_util.CliConfig.get().org}-{bgnr_util.CliConfig.get().project}-global-stack'
            bgnr_util.Out.trace('aws cloudformation describe-stacks --stack-name bgm-nerdrock-global-stack')
            stack = cf_client.describe_stacks(StackName=stack_name)['Stacks'][0]
            kvs_arn = next(val for x in stack.get('Outputs') or [] if (
                x.get('OutputKey') == 'KeyValueStoreArn' and
                (val := x.get('OutputValue')) is not None
            ))
            kvs_client: boto3_cfront_kvs.CloudFrontKeyValueStoreClient = boto3.client('cloudfront-keyvaluestore')
            bgnr_util.Out.trace(f'aws cloudfront-keyvaluestore describe-key-value-store --kvs-arn {kvs_arn}')
            etag = kvs_client.describe_key_value_store(KvsARN=kvs_arn)['ETag']
            bgnr_util.Out.trace('aws cloudfront-keyvaluestore put-key '
                                '--key {bgnr_util.Config.get().allowed_ips_key} '
                                '--value {ipv4} '
                                '--kvs-arn {kvs_arn} '
                                '--if-match {etag}')
            kvs_client.put_key(Key=bgnr_util.CliConfig.get().allowed_ips_key, Value=','.join([ipv4, ipv6]),
                               KvsARN=kvs_arn, IfMatch=etag)
