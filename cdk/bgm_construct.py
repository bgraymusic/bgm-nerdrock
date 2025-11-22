"""BGM construct base class and concrete implementations of distribution constructs"""

import pathlib
import re
import typing

import aws_cdk
from aws_cdk import aws_apigateway, aws_cloudfront, aws_cloudfront_origins, aws_route53, aws_route53_targets, aws_s3
import constructs as aws_constructs

import cdk.bgm_context as bgm_context
import cdk.bgm_stack as bgm_stack


class BgmConstruct(aws_constructs.Construct):
    """Base class for all BGM constructs"""

    def __init__(self, scope: aws_constructs.Construct, construct_id: str, context: bgm_context.BgmContext) -> None:
        super().__init__(scope, construct_id)
        self.project_directory = pathlib.Path(__file__).parent
        self.context = context

    def logical_id_for(self, construct_id: str):
        return self.context.logical_id_for(construct_id)

    def physical_id_for(self, construct_id: str):
        return self.context.physical_id_for(construct_id)

    def capitalize(self, s: str):
        s = re.sub(r'[\W]', '', s)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)


class DistributionConstruct(BgmConstruct):
    """CDK construct to create the distribution for the app"""

    def __init__(
            self, scope: aws_constructs.Construct, construct_id: str, context: bgm_context.EnvContext,
            bucket: aws_s3.Bucket, api: aws_apigateway.RestApi, blockRemoteAccess: bool = False
        ) -> None:
        super().__init__(scope, construct_id, context)

        env_stack = aws_cdk.Stack.of(self)
        assert isinstance(env_stack, bgm_stack.EnvStack)
        global_stack: bgm_stack.GlobalStack = env_stack.global_stack

        if blockRemoteAccess:
            func = aws_cloudfront.Function(
                self, context.logical_id_for('NonProdCFFunction'), key_value_store=global_stack.kv_store,
                code=aws_cloudfront.FunctionCode.from_file(file_path=context.non_prod_func_path),
                function_name=context.physical_id_for('non-prod-cf-func')
            )
        else:
            func = aws_cloudfront.Function(
                self, context.logical_id_for('ProdCFFunction'), key_value_store=global_stack.kv_store,
                code=aws_cloudfront.FunctionCode.from_file(file_path=context.prod_func_path),
                function_name=context.physical_id_for('prod-cf-func')
            )

        self.distribution = aws_cloudfront.Distribution(
            self, context.logical_id_for('Distribution'),
            comment=context.physical_id_for('distribution'),
            default_root_object='index.html', enable_logging=True,
            default_behavior=aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.S3StaticWebsiteOrigin(
                    bucket, origin_id=context.physical_id_for('website-origin')
                ),
                function_associations=[aws_cloudfront.FunctionAssociation(
                    event_type=aws_cloudfront.FunctionEventType.VIEWER_REQUEST, function=func
                )]),
            additional_behaviors={'api/*': aws_cloudfront.BehaviorOptions(
                origin=aws_cloudfront_origins.RestApiOrigin(api, origin_id=context.physical_id_for('api-origin')),
                origin_request_policy=aws_cloudfront.OriginRequestPolicy.CORS_CUSTOM_ORIGIN,
                response_headers_policy=aws_cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT
                )},
            certificate=global_stack.certificate, domain_names=[context.host_name]
        )
        cf_target: aws_route53.IAliasRecordTarget = \
            typing.cast(aws_route53.IAliasRecordTarget, aws_route53_targets.CloudFrontTarget(self.distribution))
        aws_route53.ARecord(
            self, 'ARecord', zone=global_stack.hosted_zone, record_name=context.host_name,
            target=aws_route53.RecordTarget.from_alias(cf_target)
        )
        aws_route53.AaaaRecord(
            self, 'AaaaRecord', zone=global_stack.hosted_zone, record_name=context.host_name,
            target=aws_route53.RecordTarget.from_alias(cf_target)
        )
        aws_cdk.CfnOutput(self, 'Distribution', value=self.distribution.domain_name)


class NonProdDistributionConstruct(DistributionConstruct):
    def __init__(
        self, scope: aws_constructs.Construct, construct_id: str, context: bgm_context.EnvContext,
        bucket: aws_s3.Bucket, api: aws_apigateway.RestApi
    ):
        super().__init__(scope, construct_id, context, bucket, api, True)

