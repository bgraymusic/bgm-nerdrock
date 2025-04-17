from typing import List

from aws_cdk import Aws, Stack, Duration, CfnOutput, RemovalPolicy
from aws_cdk.aws_apigateway import (
    RestApi, Resource, LambdaIntegration, PassthroughBehavior,
    Method, MethodOptions, MethodResponse, IntegrationResponse, CorsOptions, Cors
)
from aws_cdk.aws_events import Rule, Schedule, RuleTargetInput
from aws_cdk.aws_events_targets import LambdaFunction
from aws_cdk.aws_iam import Role, ManagedPolicy, ServicePrincipal
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_logs import LogGroup
from constructs import Construct

from cdk.bgm_construct import BgmConstruct
from cdk.bgm_context import EnvContext
from api.runtime.handler_base import HandlerBase, HandlerDescription


class APIConstruct(BgmConstruct):
    request_templates = {
        'badges': {'application/json': "{}"},
        'discography': {'application/json': "{}"},
        '{token}': {'application/json': "{ \"token\": \"$input.params().path['token']\" }"},
        '{key}': {'application/json':
                  "{ \"token\": \"$input.params().path['token']\", \"key\": \"$input.params().path['key']\" }"
                  }
    }

    def __init__(self, scope: Construct, id: str, context: EnvContext):
        super().__init__(scope, id, context)

        self.restApi, apiResourceRoot = self.createApiRoot()
        lambdaRole: Role = self.createLambdaRole()
        self.lambdas = []
        globalStack = Stack.of(self).globalStack

        # Create lambda functions
        for handlerClass in HandlerBase.__subclasses__():
            description: HandlerDescription = handlerClass.describe()
            logGroup = LogGroup(self, f'{self.capitalize(description.name)}LogGroup',
                                log_group_name=self.physicalIdFor(f'{description.name}-log-group'),
                                removal_policy=RemovalPolicy.DESTROY)
            function = Function(
                self, f'{self.capitalize(description.name)}Lambda', role=lambdaRole,
                function_name=self.physicalIdFor(description.name), timeout=Duration.seconds(30),
                handler=f'{handlerClass.__module__}.handle', runtime=Runtime.PYTHON_3_13,
                code=Code.from_asset(self.context.lambdaPackage, deploy_time=True),
                environment={
                    'stackName': Aws.STACK_NAME,
                    'log_level': 'DEBUG',
                    'config': 'api/config.yml',
                    # 'secretsBucket': f'{self.context.org}-{self.context.project}-secrets',
                    'secretsBucket': globalStack.secretsBucket.bucket_name,
                    'secretsFile': 'secrets.yml',
                    'tablePrefix': f'{self.context.org}-{self.context.project}-{self.context.env}'
                }, log_group=logGroup
            )
            self.lambdas.append((handlerClass, function))
            CfnOutput(self, f'{self.capitalize(description.name)}LambdaName', value=function.function_name)

            parent = apiResourceRoot
            parentLogical = ''
            for resourceSpec in description.resources:
                resourceLogical = f'{self.capitalize(parentLogical)}{self.capitalize(resourceSpec.path)}'
                resource = Resource(self,
                                    resourceLogical,
                                    parent=parent,
                                    path_part=resourceSpec.path)
                for methodSpec in resourceSpec.methods:
                    Method(self,
                           f'{resourceLogical}{methodSpec.method._name_}',
                           http_method=methodSpec.method._name_,
                           resource=resource,
                           integration=LambdaIntegration(
                               function, proxy=False, passthrough_behavior=PassthroughBehavior.NEVER,
                               request_templates=self.request_templates[resourceSpec.path],
                               integration_responses=self.integrationResponses(methodSpec.errors)),
                           options=MethodOptions(method_responses=self.methodResponses(methodSpec.errors)))
                parentLogical = resourceLogical
                parent = resource

    def createApiRoot(self):
        restApi: RestApi = RestApi(
            self, 'RestApi', rest_api_name=self.physicalIdFor('api'),
            # default_cors_preflight_options=CorsOptions(allow_origins=Cors.ALL_ORIGINS)
        )
        resourceRoot: Resource = Resource(self, 'ResourceRoot', parent=restApi.root, path_part='api')
        return restApi, resourceRoot

    def createLambdaRole(self) -> Role:
        return Role(self, self.logicalIdFor('lambdaRole'),
                    assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                    role_name=self.physicalIdFor('lambda-role'),
                    managed_policies=[
                        ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                        ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaVPCAccessExecutionRole'),
                        ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'),
                        ManagedPolicy.from_aws_managed_policy_name('AmazonS3ReadOnlyAccess')
                    ])

    def methodResponses(self, errors: List[Exception]) -> List[MethodResponse]:
        result = [MethodResponse(status_code='200', response_parameters={'method.response.header.Content-Type': True})]
        for error in errors:
            result.append(MethodResponse(
                status_code=str(error.code),
                response_parameters={'method.response.header.Content-Type': True}))
        return result

    def integrationResponses(self, errors: List[Exception]) -> List[IntegrationResponse]:
        result = [IntegrationResponse(status_code='200', selection_pattern='',
                                      response_parameters={'method.response.header.Content-Type': "'application/json'"},
                                      response_templates={'application/json': "$input.json('$')"})]
        for error in errors:
            result.append(IntegrationResponse(
                status_code=str(error.code),
                selection_pattern=f'.*{error.__name__}.*',
                response_parameters={'method.response.header.Content-Type': "'application/json'"},
                response_templates={
                    'application/json':
                        "$input.path('$.errorMessage').replaceAll(\"'\", '\"').replaceAll('None', '\"\"')"}))
        return result


class ProdAPIConstruct(APIConstruct):
    def __init__(self, scope: Construct, id: str, context: EnvContext):
        super().__init__(scope, id, context)

        keepWarm = Rule(self, 'KeepWarm', schedule=Schedule.rate(Duration.minutes(5)),
                        rule_name=self.physicalIdFor('keep-warm'))
        for handlerClass, function in self.lambdas:
            if handlerClass.describe().keepWarm:
                keepWarm.add_target(LambdaFunction(function, event=RuleTargetInput.from_object({
                    "keep_warm": True
                })))
