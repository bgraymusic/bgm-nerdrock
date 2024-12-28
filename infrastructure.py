import pathlib
import re

from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_apigateway import RestApi
from aws_cdk.aws_cloudfront import (
  Distribution, HttpVersion, PriceClass, BehaviorOptions, AllowedMethods, CachedMethods, ViewerProtocolPolicy
)
from aws_cdk.aws_cloudfront_origins import S3StaticWebsiteOrigin, RestApiOrigin
from constructs import Construct


class BgmContext():
    def __init__(self, stage: str = 'dev', webPackage: str = None, lambdaPackage: str = None):
        self.org = 'bgm'
        self.project = 'nerdrock'
        self.stage = stage
        self.logicalIdPrefix = ''.join([BgmConstruct.capitalize(x) for x in [self.org, self.project, self.stage]])
        self.physicalIdPrefix = f'{self.org.lower()}-{self.project.lower()}-{self.stage.lower()}'
        self.lambdaPackage = lambdaPackage if lambdaPackage else f'./{self.physicalIdPrefix}-lambdas.zip'
        self.webPackage = webPackage if webPackage else f'./{self.physicalIdPrefix}-web.zip'

    def logicalIdFor(self, id: str):
        return f'{self.logicalIdPrefix}{BgmConstruct.capitalize(id)}'

    def physicalIdFor(self, id: str):
        return f'{self.physicalIdPrefix}-{id}'

    def getTags(self):
        return {'org': self.org, 'project': self.project, 'stage': self.stage}


class BgmConstruct(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        self.projectDirectory = pathlib.Path(__file__).parent

    @staticmethod
    def capitalize(str):
        str = re.sub(r'[\W]', '', str)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), str, 1)


class DistributionConstruct(BgmConstruct):
    def __init__(self, scope: Construct, id: str, stage: str, bucket: Bucket, api: RestApi) -> None:
        super().__init__(scope, id)
        self.distribution = Distribution(
            self, 'RestApiDistribution', enabled=True, http_version=HttpVersion.HTTP2_AND_3,
            price_class=PriceClass.PRICE_CLASS_ALL, default_root_object='index.html',
            default_behavior=BehaviorOptions(
                origin=S3StaticWebsiteOrigin(bucket),
                allowed_methods=AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=CachedMethods.CACHE_GET_HEAD_OPTIONS,
                compress=True,
                viewer_protocol_policy=ViewerProtocolPolicy.REDIRECT_TO_HTTPS),
            additional_behaviors={stage: BehaviorOptions(
                origin=RestApiOrigin(api),
                allowed_methods=AllowedMethods.ALLOW_GET_HEAD,
                cached_methods=CachedMethods.CACHE_GET_HEAD,
                viewer_protocol_policy=ViewerProtocolPolicy.REDIRECT_TO_HTTPS)
            })
