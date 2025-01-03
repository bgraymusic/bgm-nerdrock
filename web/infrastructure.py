from aws_cdk import RemovalPolicy, CfnOutput
from aws_cdk.aws_cloudfront import IDistribution
from aws_cdk.aws_s3 import Bucket, BlockPublicAccess
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from constructs import Construct
from infrastructure import BgmConstruct, BgmContext


class WebConstruct(BgmConstruct):
    def __init__(self, scope: Construct, id: str, context: BgmContext):
        super().__init__(scope, id)

        # Nerdrock Static Web Site Bucket
        self.website_bucket = Bucket(
            self, 'S3Bucket', bucket_name=context.physicalIdFor('web'),
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            website_index_document='index.html', website_error_document='error.html',
            # counterintuitively allows public access
            block_public_access=BlockPublicAccess(block_public_acls=True), public_read_access=True,
        )
        CfnOutput(self, 'Bucket', value=self.website_bucket.bucket_name)

    def deployWebSite(self, distribution: IDistribution, context: BgmContext):
        # Deploy Website to Bucket
        BucketDeployment(
            self, 'Deploy', destination_bucket=self.website_bucket,
            sources=[Source.asset(context.webPackage)],
            distribution=distribution, extract=True)
