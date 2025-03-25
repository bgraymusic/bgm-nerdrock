from pathlib import Path
import re

from aws_cdk import CfnOutput, Stack
from aws_cdk.aws_apigateway import RestApi
from aws_cdk.aws_cloudfront import Distribution, BehaviorOptions, FunctionAssociation, FunctionEventType
from aws_cdk.aws_cloudfront_origins import S3StaticWebsiteOrigin, RestApiOrigin
from aws_cdk.aws_route53 import ARecord, AaaaRecord, RecordTarget
from aws_cdk.aws_route53_targets import CloudFrontTarget
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

from .bgm_context import BgmContext, EnvContext


class BgmConstruct(Construct):
    def __init__(self, scope: Construct, id: str, context: BgmContext) -> None:
        super().__init__(scope, id)
        self.projectDirectory = Path(__file__).parent
        self.context = context

    def logicalIdFor(self, id: str):
        return self.context.logicalIdFor(id)

    def physicalIdFor(self, id: str):
        return self.context.physicalIdFor(id)

    def capitalize(self, s: str):
        s = re.sub(r'[\W]', '', s)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)


class DistributionConstruct(BgmConstruct):
    def __init__(self, scope: Construct, id: str, context: EnvContext, bucket: Bucket, api: RestApi,
                 blockRemoteAccess: bool = False) -> None:
        super().__init__(scope, id, context)

        globalStack = Stack.of(self).globalStack

        function_associations = [
            FunctionAssociation(event_type=FunctionEventType.VIEWER_REQUEST, function=globalStack.restRoutingFunction),
            FunctionAssociation(event_type=FunctionEventType.VIEWER_REQUEST, function=globalStack.blockIpFunction)
        ] if blockRemoteAccess else [
            FunctionAssociation(event_type=FunctionEventType.VIEWER_REQUEST, function=globalStack.restRoutingFunction)
        ]

        self.distribution = Distribution(
            self, context.logicalIdFor('Distribution'),
            comment=context.physicalIdFor('distribution'),
            default_root_object='index.html',
            default_behavior=BehaviorOptions(
                origin=S3StaticWebsiteOrigin(bucket, origin_id=context.physicalIdFor('website-origin')),
                function_associations=function_associations),
            additional_behaviors={'api/*': BehaviorOptions(
                origin=RestApiOrigin(api, origin_id=context.physicalIdFor('api-origin')))},
            certificate=globalStack.certificate, domain_names=[context.hostName]
        )
        ARecord(self, 'ARecord', zone=globalStack.hostedZone, record_name=context.hostName,
                target=RecordTarget.from_alias(CloudFrontTarget(self.distribution)))
        AaaaRecord(self, 'AaaaRecord', zone=globalStack.hostedZone, record_name=context.hostName,
                   target=RecordTarget.from_alias(CloudFrontTarget(self.distribution)))
        CfnOutput(self, 'Distribution', value=self.distribution.domain_name)


class NonProdDistributionConstruct(DistributionConstruct):
    def __init__(self, scope: Construct, id: str, context: EnvContext, bucket: Bucket, api: RestApi):
        super().__init__(scope, id, context, bucket, api, True)

