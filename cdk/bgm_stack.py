import json
import os
from pathlib import Path

from aws_cdk import Stack, Environment, Tags, RemovalPolicy, CfnOutput
from aws_cdk.aws_certificatemanager import Certificate, CertificateValidation
from aws_cdk.aws_cloudfront import KeyValueStore, ImportSource, Function, FunctionCode, FunctionRuntime
from aws_cdk.aws_route53 import HostedZone
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_ssm import StringParameter, StringListParameter
from constructs import Construct

from .bgm_construct import DistributionConstruct, NonProdDistributionConstruct
from .bgm_context import BgmContext, GlobalContext, EnvContext
from api.infrastructure import APIConstruct, ProdAPIConstruct
from db import DbConstruct
from web import WebConstruct


class BgmStack(Stack):
    def __init__(self, scope: Construct, context: BgmContext) -> None:
        super().__init__(scope, context.logicalIdFor('stack'), stack_name=context.physicalIdFor('stack'),
                         env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                                         region=os.getenv('CDK_DEFAULT_REGION')))
        self.projectDirectory: Path = Path(__file__).parent.parent
        self.context: BgmContext = context
        for tag, val in self.context.getTags().items():
            Tags.of(self).add(tag, val)

    # Get rid of those appended hashes that ensure that no two logical IDs conflict. They make output keys
    # hard to predict and clutter things up. If I fuck up and produce conflicts, the build will tell me.
    def _allocate_logical_id(self, cfn_element):
        return super()._allocate_logical_id(cfn_element)[:-8]

    def logicalIdFor(self, id: str):
        return self.context.logicalIdFor(id)

    def physicalIdFor(self, id: str):
        return self.context.physicalIdFor(id)


class GlobalStack(BgmStack):
    def __init__(self, scope: Construct, context: GlobalContext, ssmParams: dict, kvPairs: dict) -> None:
        super().__init__(scope, context)

        self.secretsBucket = Bucket(self, 'SecretsBucket', bucket_name=ssmParams['secrets-bucket'],
                                    removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True)
        CfnOutput(self, 'SecretsBucketName', value=self.secretsBucket.bucket_name, key='SecretsBucketName')

        for key, value in ssmParams.items():
            if isinstance(value, list):
                StringListParameter(self, self.logicalIdFor(key), string_list_value=value,
                                    parameter_name=f'{context.org}-{context.project}-{key}')
            else:
                StringParameter(self, self.logicalIdFor(key), string_value=value,
                                parameter_name=f'{context.org}-{context.project}-{key}')

        kvData = [{"key": key, "value": value} for key, value in kvPairs.items()]
        kvStore = KeyValueStore(self, 'KeyValueStore', key_value_store_name=self.physicalIdFor('kv-store'),
                                source=ImportSource.from_inline(json.dumps({"data": kvData})))
        CfnOutput(self, 'KeyValueStoreArn', value=kvStore.key_value_store_arn, key='KeyValueStoreArn')

        self.blockIpFunction = Function(self, 'BlockIpFunction', key_value_store=kvStore,
                                        code=FunctionCode.from_file(file_path=context.blockIpCfFuncPath))
        self.restRoutingFunction = Function(self, 'RestRoutingFunction', runtime=FunctionRuntime.FunctionRuntime.JS_2_0,
                                            code=FunctionCode.from_file(file_path=context.restRoutingCfFuncPath))
        self.hostedZone = HostedZone(self, 'HostedZone', zone_name=context.domain)
        self.hostedZone.apply_removal_policy(RemovalPolicy.RETAIN_ON_UPDATE_OR_DELETE)
        self.certificate = Certificate(self, 'Certificate', domain_name=self.context.domain,
                                       subject_alternative_names=[f'*.{self.context.domain}'],
                                       validation=CertificateValidation.from_dns(self.hostedZone))


class EnvStack(BgmStack):
    def __init__(self, scope: Construct, context: EnvContext, globalStack: GlobalStack) -> None:
        super().__init__(scope, context)

        self.globalStack = globalStack
        DbConstruct(self, id=self.logicalIdFor('db'), context=context)
        self.web = WebConstruct(self, id=self.logicalIdFor('web'), context=context)


class ProdEnvStack(EnvStack):
    def __init__(self, scope: Construct, context: EnvContext, globalStack: GlobalStack):
        super().__init__(scope, context, globalStack)

        api = ProdAPIConstruct(self, id=self.logicalIdFor('api'), context=context)
        distribution = DistributionConstruct(self, id=self.logicalIdFor('distro'), context=context,
                                             bucket=self.web.website_bucket, api=api.restApi)
        self.web.deployWebSite(distribution=distribution.distribution)


class NonProdEnvStack(EnvStack):
    def __init__(self, scope: Construct, context: EnvContext, globalStack: GlobalStack):
        super().__init__(scope, context, globalStack)

        api = APIConstruct(self, id=self.logicalIdFor('api'), context=context)
        distribution = NonProdDistributionConstruct(self, id=self.logicalIdFor('distro'), context=context,
                                                    bucket=self.web.website_bucket, api=api.restApi)
        self.web.deployWebSite(distribution=distribution.distribution)
