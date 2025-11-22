"""CDK Construct definitions for the NerdRock Rest API"""

import typing

import aws_cdk
from aws_cdk import aws_apigateway, aws_events, aws_events_targets, aws_iam, aws_lambda, aws_logs
import constructs as aws_constructs

from cdk import bgm_construct
from cdk import bgm_context
from cdk import bgm_stack
from api.runtime import handler_base


class APIConstruct(bgm_construct.BgmConstruct):
    """Common construct definition for all environment types"""

    request_templates = {
        'badges': {'application/json': '{}'},
        'discography': {'application/json': '{}'},
        '{token}': {'application/json': '{ "token": "$input.params().path[\'token\']" }'},
        '{key}': {'application/json':
                  '{ "token": "$input.params().path[\'token\']", "key": "$input.params().path[\'key\']" }'
                  }
    }

    def __init__(self, scope: aws_constructs.Construct, construct_id: str, context: bgm_context.EnvContext):
        super().__init__(scope, construct_id, context)

        self.env_context = context
        self.rest_api, api_resource_root = self.create_api_root()
        lambda_role: aws_iam.IRole = self.create_lambda_role()
        self.lambdas = []
        env_stack = aws_cdk.Stack.of(self)
        assert isinstance(env_stack, bgm_stack.EnvStack)
        global_stack: bgm_stack.GlobalStack = env_stack.global_stack

        # Create lambda functions
        for handler_class in handler_base.HandlerBase.__subclasses__():
            description: handler_base.HandlerDescription = handler_class.describe()
            log_group = aws_logs.LogGroup(self, f'{self.capitalize(description.name)}LogGroup',
                                log_group_name=self.physical_id_for(f'{description.name}-log-group'),
                                removal_policy=aws_cdk.RemovalPolicy.DESTROY)
            function = aws_lambda.Function(
                self, f'{self.capitalize(description.name)}Lambda', role=lambda_role,
                function_name=self.physical_id_for(description.name), timeout=aws_cdk.Duration.seconds(30),
                handler=f'{handler_class.__module__}.handle', runtime=aws_lambda.Runtime.PYTHON_3_13,
                code=aws_lambda.Code.from_asset(self.env_context.lambda_package, deploy_time=True),
                environment = {
                    'stackName': aws_cdk.Aws.STACK_NAME,
                    'log_level': 'DEBUG',
                    'config': 'api/config.yml',
                    # 'secretsBucket': f'{self.context.org}-{self.context.project}-secrets',
                    'secretsBucket': global_stack.secrets_bucket.bucket_name,
                    'secretsFile': 'secrets.yml',
                    'tablePrefix': f'{self.context.org}-{self.context.project}-{self.env_context.env}'
                }, log_group=log_group
            )
            self.lambdas.append((handler_class, function))
            aws_cdk.CfnOutput(self, f'{self.capitalize(description.name)}LambdaName', value=function.function_name)

            parent = api_resource_root
            parent_logical = ''
            for resource_spec in description.resources:
                resource_logical = f'{self.capitalize(parent_logical)}{self.capitalize(resource_spec.path)}'
                resource = aws_apigateway.Resource(self,
                                    resource_logical,
                                    parent=typing.cast(aws_apigateway.IResource, parent),
                                    path_part=resource_spec.path)
                for method_spec in resource_spec.methods:
                    aws_apigateway.Method(self,
                        f'{resource_logical}{method_spec.method._name_}',
                        http_method=method_spec.method._name_,
                        resource=typing.cast(aws_apigateway.IResource, resource),
                        integration=aws_apigateway.LambdaIntegration(
                            typing.cast(aws_lambda.IFunction, function), proxy=False,
                            passthrough_behavior=aws_apigateway.PassthroughBehavior.NEVER,
                            request_templates=self.request_templates[resource_spec.path],
                            integration_responses=self.integration_responses(method_spec.errors)),
                        options=aws_apigateway.MethodOptions(
                            method_responses=self.method_responses(method_spec.errors)
                        )
                    )
                parent_logical = resource_logical
                parent = resource

    def create_api_root(self):
        rest_api: aws_apigateway.RestApi = aws_apigateway.RestApi(
            self, 'RestApi', rest_api_name=self.physical_id_for('api'),
            # default_cors_preflight_options=CorsOptions(allow_origins=Cors.ALL_ORIGINS)
        )
        resource_root: aws_apigateway.Resource = aws_apigateway.Resource(
            self, 'ResourceRoot', parent=rest_api.root, path_part='api'
        )
        return rest_api, resource_root

    def create_lambda_role(self) -> aws_iam.IRole:
        return typing.cast(aws_iam.IRole, aws_iam.Role(self, self.logical_id_for('lambdaRole'),
                    assumed_by=typing.cast(aws_iam.IPrincipal, aws_iam.ServicePrincipal('lambda.amazonaws.com')),
                    role_name=self.physical_id_for('lambda-role'),
                    managed_policies=[
                        aws_iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                        aws_iam.ManagedPolicy.from_aws_managed_policy_name(
                            'service-role/AWSLambdaVPCAccessExecutionRole'
                        ),
                        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'),
                        aws_iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
                    ]))

    def method_responses(self, errors: list[type[handler_base.BgnrError]]) -> list[aws_apigateway.MethodResponse]:
        result = [aws_apigateway.MethodResponse(
            status_code='200', response_parameters={'method.response.header.Content-Type': True}
        )]
        for error in errors:
            result.append(aws_apigateway.MethodResponse(
                status_code=str(error.code),
                response_parameters={'method.response.header.Content-Type': True}))
        return result

    def integration_responses(
        self, errors: list[type[handler_base.BgnrError]]
    ) -> list[aws_apigateway.IntegrationResponse]:
        result = [aws_apigateway.IntegrationResponse(status_code='200', selection_pattern='',
                                      response_parameters={'method.response.header.Content-Type': "'application/json'"},
                                      response_templates={'application/json': "$input.json('$')"})]
        for error in errors:
            result.append(aws_apigateway.IntegrationResponse(
                status_code=str(error.code),
                selection_pattern=f'.*{error.__class__.__name__}.*',
                response_parameters={'method.response.header.Content-Type': "'application/json'"},
                response_templates={
                    'application/json':
                        "$input.path('$.errorMessage').replaceAll(\"'\", '\"').replaceAll('None', '\"\"')"}))
        return result


class ProdAPIConstruct(APIConstruct):
    """Specific construct modifications for production APIs"""

    def __init__(self, scope: aws_constructs.Construct, construct_id: str, context: bgm_context.EnvContext):
        super().__init__(scope, construct_id, context)

        keep_warm = aws_events.Rule(self, 'KeepWarm', schedule=aws_events.Schedule.rate(aws_cdk.Duration.minutes(5)),
                        rule_name=self.physical_id_for('keep-warm'))
        for handler_class, function in self.lambdas:
            if handler_class.describe().keepWarm:
                keep_warm.add_target(typing.cast(
                    aws_events.IRuleTarget,
                    aws_events_targets.LambdaFunction(function, event=aws_events.RuleTargetInput.from_object({
                        'keep_warm': True
                    }))
                ))
