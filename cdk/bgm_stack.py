"""Base class and all CDK stack definitions for the app"""

import json
import os
import pathlib

import aws_cdk
from aws_cdk import aws_certificatemanager, aws_cloudfront, aws_route53, aws_s3, aws_ssm
import constructs as aws_constructs

from cdk import bgm_config, bgm_construct, bgm_context
import api.infrastructure as bgm_api
import db as bgm_db
import web as bgm_web


class BgmStack(aws_cdk.Stack):
    """Base class for all stacks, establishing the CDK account/region and common context"""

    def __init__(self, scope: aws_constructs.Construct, context: bgm_context.BgmContext) -> None:
        super().__init__(scope, context.logical_id_for('stack'), stack_name=context.physical_id_for('stack'),
                         description=context.get_stack_description(),
                         env=aws_cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                                         region=os.getenv('CDK_DEFAULT_REGION')))
        self.project_directory: pathlib.Path = pathlib.Path(__file__).parent.parent
        self.context: bgm_context.BgmContext = context
        for tag, val in self.context.get_tags().items():
            aws_cdk.Tags.of(self).add(tag, val)

    # Get rid of those appended hashes that ensure that no two logical IDs conflict. They make output keys
    # hard to predict and clutter things up. If I fuck up and produce conflicts, the build will tell me.
    def _allocate_logical_id(self, cfn_element):
        return super()._allocate_logical_id(cfn_element)[:-8]

    def logical_id_for(self, construct_id: str):
        return self.context.logical_id_for(construct_id)

    def physical_id_for(self, construct_id: str):
        return self.context.physical_id_for(construct_id)


class GlobalStack(BgmStack):
    """Implementation of the global stack, which contains data and services for all environments"""

    def __init__(
        self, scope: aws_constructs.Construct, context: bgm_context.GlobalContext, config: bgm_config.BgmConfig
    ) -> None:
        super().__init__(scope, context)

        self.secrets_bucket = aws_s3.Bucket(self, 'SecretsBucket', bucket_name=config.ssm_parameters.secrets_bucket,
                                    removal_policy=aws_cdk.RemovalPolicy.DESTROY, auto_delete_objects=True)
        aws_cdk.CfnOutput(self, 'SecretsBucketName', value=self.secrets_bucket.bucket_name, key='SecretsBucketName')

        for key, value in vars(config.ssm_parameters):
            if isinstance(value, list):
                aws_ssm.StringListParameter(self, self.logical_id_for(key), string_list_value=value,
                                    parameter_name=f'{context.org}-{context.project}-{key}')
            else:
                aws_ssm.StringParameter(self, self.logical_id_for(key), string_value=value,
                                parameter_name=f'{context.org}-{context.project}-{key}')

        kv_data = [{'key': key, 'value': value} for key, value in vars(config.key_value_pairs)]
        self.kv_store = aws_cloudfront.KeyValueStore(
            self, 'KeyValueStore', key_value_store_name=self.physical_id_for('kv-store'),
            source=aws_cloudfront.ImportSource.from_inline(json.dumps({'data': kv_data}))
        )
        aws_cdk.CfnOutput(self, 'KeyValueStoreArn', value=self.kv_store.key_value_store_arn, key='KeyValueStoreArn')

        self.prod_func = aws_cloudfront.Function(
            self, 'RestRoutingFunction', runtime=aws_cloudfront.FunctionRuntime.JS_2_0,
            code=aws_cloudfront.FunctionCode.from_file(file_path=context.prod_func_path)
        )
        aws_cdk.CfnOutput(self, 'ProdFuncExportPlaceholder', value=self.prod_func.function_arn,
                  key='ExportsOutputFnGetAttRestRoutingFunctionFunctionARN',
                  export_name='bgm-nerdrock-global-stack:ExportsOutputFnGetAttRestRoutingFunctionFunctionARNDAC36FAC')

        self.hosted_zone = aws_route53.HostedZone(self, 'HostedZone', zone_name=context.domain)
        self.hosted_zone.apply_removal_policy(aws_cdk.RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE)
        self.certificate = aws_certificatemanager.Certificate(
            self, 'Certificate', domain_name=self.context.domain,
            subject_alternative_names=[f'*.{self.context.domain}'],
            validation=aws_certificatemanager.CertificateValidation.from_dns(self.hosted_zone)
        )
        self.blog_cname = aws_route53.CnameRecord(
            self, 'BlogCnameRecord', zone=self.hosted_zone, ttl=aws_cdk.Duration.days(1),
            record_name=self.context.blog_host_name, domain_name=self.context.blog_target_domain
        )


class EnvStack(BgmStack):
    """Base class for environment stacks, with data and config that does not differ between prod and non-prod"""

    def __init__(
        self, scope: aws_constructs.Construct, context: bgm_context.EnvContext, global_stack: GlobalStack
    ) -> None:
        super().__init__(scope, context)

        self.global_stack = global_stack
        bgm_db.DbConstruct(self, construct_id=self.logical_id_for('db'), context=context)
        self.web = bgm_web.WebConstruct(self, construct_id=self.logical_id_for('web'), context=context)


class ProdEnvStack(EnvStack):
    """Production environment stack; will auto-scale, keep warm, etc."""

    def __init__(
        self, scope: aws_constructs.Construct, context: bgm_context.EnvContext, globalStack: GlobalStack
    ) -> None:
        super().__init__(scope, context, globalStack)

        api = bgm_api.ProdAPIConstruct(self, construct_id=self.logical_id_for('api'), context=context)
        distribution = bgm_construct.DistributionConstruct(
            self, construct_id=self.logical_id_for('distro'), context=context,
            bucket=self.web.website_bucket, api=api.rest_api
        )
        self.web.deploy_web_site(distribution=distribution.distribution)


class NonProdEnvStack(EnvStack):
    """Non-production environment stack; will conserve expenses and restrict access"""

    def __init__(
        self, scope: aws_constructs.Construct, context: bgm_context.EnvContext, globalStack: GlobalStack
    ) -> None:
        super().__init__(scope, context, globalStack)

        api = bgm_api.APIConstruct(self, construct_id=self.logical_id_for('api'), context=context)
        distribution = bgm_construct.NonProdDistributionConstruct(
            self, construct_id=self.logical_id_for('distro'), context=context,
            bucket=self.web.website_bucket, api=api.rest_api
        )
        self.web.deploy_web_site(distribution=distribution.distribution)
