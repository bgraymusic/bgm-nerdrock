from typing import List

from aws_cdk import Aws, Duration
from aws_cdk.aws_apigateway import (
    RestApi, StageOptions, Resource,
    LambdaIntegration, PassthroughBehavior,
    Method, MethodOptions, MethodResponse, IntegrationResponse
)
from aws_cdk.aws_iam import Role, ManagedPolicy, ServicePrincipal
from aws_cdk.aws_lambda import Function, Runtime, Code
from aws_cdk.aws_logs import LogGroup
from constructs import Construct
from infrastructure import BgmConstruct, BgmContext
from api import HandlerBase


class APIConstruct(BgmConstruct):
    request_templates = {
        'badges': {'application/json': "{}"},
        'discography': {'application/json': "{}"},
        '{token}': {'application/json': "{ \"token\": \"$input.params().path['token']\" }"},
        '{key}': {'application/json':
                  "{ \"token\": \"$input.params().path['token']\", \"key\": \"$input.params().path['key']\" }"
                  }
    }

    def __init__(self, scope: Construct, id: str, context: BgmContext):
        super().__init__(scope, id)

        self.restApi, apiResourceRoot = self.createApiRoot(context)
        lambdaRole: Role = self.createLambdaRole(context)

        # Create lambda functions
        for handlerClass in HandlerBase.__subclasses__():
            description = handlerClass.describe()
            logGroup = LogGroup(self, f'{self.capitalize(description.name)}LogGroup',
                                log_group_name=context.physicalIdFor(f'{description.name}-log-group'))
            function = Function(
                self, f'{self.capitalize(description.name)}Lambda', role=lambdaRole,
                function_name=context.physicalIdFor(description.name), timeout=Duration.seconds(15),
                handler=f'{handlerClass.__module__}.handle', runtime=Runtime.PYTHON_3_13,
                code=Code.from_asset(context.lambdaPackage, deploy_time=True),
                environment={
                    'stackName': Aws.STACK_NAME,
                    'log_level': 'DEBUG',
                    'config': 'api/config.yml',
                    'secretsBucket': f'{context.org}-{context.project}-secrets',
                    'secretsFile': 'secrets.yml',
                    'tablePrefix': f'{context.org}-{context.project}-{context.stage}'
                }, log_group=logGroup
            )

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

    def createApiRoot(self, context: BgmContext):
        restApi: RestApi = RestApi(
            self, 'RestApi', rest_api_name=context.physicalIdFor('api'),
            deploy_options=StageOptions(stage_name=context.stage))
        resourceRoot: Resource = Resource(self, 'ResourceRoot', parent=restApi.root, path_part='api')
        return restApi, resourceRoot

    def createLambdaRole(self, context) -> Role:
        return Role(self, context.logicalIdFor('lambdaRole'),
                    assumed_by=ServicePrincipal('lambda.amazonaws.com'),
                    role_name=context.physicalIdFor('lambda-role'),
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
                selection_pattern=f'.*{error.__class__}.*',
                response_parameters={'method.response.header.Content-Type': "'application/json'"},
                response_templates={
                    'application/json':
                        "$input.path('$.errorMessage').replaceAll(\"'\", '\"').replaceAll('None', '\"\"')"}))
        return result
