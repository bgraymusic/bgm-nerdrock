import pathlib
import re

from aws_cdk import CfnOutput
from aws_cdk.aws_s3 import Bucket
from aws_cdk.aws_apigateway import RestApi
from aws_cdk.aws_certificatemanager import Certificate
from aws_cdk.aws_cloudfront import Distribution, BehaviorOptions
from aws_cdk.aws_cloudfront_origins import S3StaticWebsiteOrigin, RestApiOrigin
from aws_cdk.aws_route53 import HostedZone, ARecord, AaaaRecord, RecordTarget
from aws_cdk.aws_route53_targets import CloudFrontTarget
from constructs import Construct


class BgmContext():
    def __init__(self, env: str = 'dev', webPackage: str = None, lambdaPackage: str = None, certArn: str = None):
        self.org = 'bgm'
        self.project = 'nerdrock'
        self.env = env
        self.prod = env in ['prod', 'staging']
        self.logicalIdPrefix = ''.join([BgmConstruct.capitalize(x) for x in [self.org, self.project, self.env]])
        self.physicalIdPrefix = f'{self.org.lower()}-{self.project.lower()}-{self.env.lower()}'
        self.lambdaPackage = lambdaPackage if lambdaPackage else f'./{self.physicalIdPrefix}-lambdas.zip'
        self.webPackage = webPackage if webPackage else f'./{self.physicalIdPrefix}-web.zip'
        self.domain = f'{env}.briangraymusic.com'
        self.certArn = certArn

    def logicalIdFor(self, id: str):
        return f'{self.logicalIdPrefix}{BgmConstruct.capitalize(id)}'

    def physicalIdFor(self, id: str):
        return f'{self.physicalIdPrefix}-{id}'

    def getTags(self):
        return {'org': self.org, 'project': self.project, 'env': self.env, 'app': self.physicalIdPrefix}


class BgmConstruct(Construct):
    def __init__(self, scope: Construct, id: str) -> None:
        super().__init__(scope, id)
        self.projectDirectory = pathlib.Path(__file__).parent

    @staticmethod
    def capitalize(str):
        str = re.sub(r'[\W]', '', str)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), str, 1)


class DistributionConstruct(BgmConstruct):
    def __init__(self, scope: Construct, id: str, context: BgmContext, bucket: Bucket, api: RestApi) -> None:
        super().__init__(scope, id)
        cert = Certificate.from_certificate_arn(self, 'Certificate', context.certArn)
        self.distribution = Distribution(
            self, context.logicalIdFor('Distribution'),
            comment=context.physicalIdFor('distribution'),
            default_root_object='index.html',
            default_behavior=BehaviorOptions(
                origin=S3StaticWebsiteOrigin(bucket, origin_id=context.physicalIdFor('website-origin'))),
            additional_behaviors={'api/*': BehaviorOptions(
                origin=RestApiOrigin(api, origin_id=context.physicalIdFor('api-origin')))},
            certificate=cert, domain_names=[context.domain]
        )
        zone: HostedZone = HostedZone.from_hosted_zone_attributes(self, 'HostedZone',
            hosted_zone_id='Z0624588WF0W5XTXQC7U', zone_name='briangraymusic.com')
        ARecord(self, 'ARecord', zone=zone, target=RecordTarget.from_alias(CloudFrontTarget(self.distribution)))
        AaaaRecord(self, 'AaaaRecord', zone=zone, target=RecordTarget.from_alias(CloudFrontTarget(self.distribution)))
        CfnOutput(self, 'Distribution', value=self.distribution.domain_name)
