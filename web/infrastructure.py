from aws_cdk import (
  RemovalPolicy,
  aws_s3 as S3, aws_s3_deployment as S3Deploy,
  aws_cloudfront as CloudFront
)
from constructs import Construct
from infrastructure import BgmConstruct, BgmContext


class WebConstruct(BgmConstruct):
    def __init__(self, scope: Construct, id: str, context: BgmContext):
        super().__init__(scope, id)

        # Nerdrock Static Web Site Bucket
        self.website_bucket = S3.Bucket(
            self, 'S3Bucket', bucket_name=context.physicalIdFor('web'),
            website_index_document='index.html', website_error_document='error.html',
            block_public_access=S3.BlockPublicAccess(),  # counterintuitively allows public access
            public_read_access=True, removal_policy=RemovalPolicy.DESTROY)

    def deployWebSite(self, distribution: CloudFront.IDistribution):
        # Deploy Website to Bucket
        S3Deploy.BucketDeployment(
            self, 'Deploy', destination_bucket=self.website_bucket,
            sources=[S3Deploy.Source.asset(f'{self.projectDirectory}/web.zip')],
            distribution=distribution, extract=True)
