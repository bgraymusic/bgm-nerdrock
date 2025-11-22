"""CDK Construct definitions for the NerdRock web site"""

from aws_cdk import RemovalPolicy, CfnOutput
from aws_cdk.aws_cloudfront import IDistribution
from aws_cdk.aws_s3 import Bucket, BlockPublicAccess
from aws_cdk.aws_s3_deployment import BucketDeployment, Source
from constructs import Construct

from cdk import bgm_construct
from cdk import bgm_context


class WebConstruct(bgm_construct.BgmConstruct):
    """CDK Construct definitions for the NerdRock web site"""

    def __init__(self, scope: Construct, construct_id: str, context: bgm_context.EnvContext):
        super().__init__(scope, construct_id, context)
        self.env_context = context

        # Nerdrock Static Web Site Bucket
        self.website_bucket = Bucket(
            self, 'S3Bucket', bucket_name=self.context.physical_id_for('web').lower(),
            removal_policy=RemovalPolicy.DESTROY, auto_delete_objects=True,
            website_index_document='index.html', website_error_document='error.html',
            # counterintuitively allows public access
            block_public_access=BlockPublicAccess(block_public_acls=True), public_read_access=True,
        )
        CfnOutput(self, 'Bucket', value=self.website_bucket.bucket_name)

    def deploy_web_site(self, distribution: IDistribution):
        # Deploy Website to Bucket
        BucketDeployment(self, 'Deploy', destination_bucket=self.website_bucket,
                         sources=[Source.asset(self.env_context.web_package)], distribution=distribution, extract=True)
