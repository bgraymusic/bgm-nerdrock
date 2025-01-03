#!/usr/bin/env python3

import os
import sys
import pathlib
from aws_cdk import App, Stack, Environment, Tags
from constructs import Construct

from infrastructure import DistributionConstruct, BgmContext
from db import DbConstruct
from api.infrastructure import APIConstruct
from web import WebConstruct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stack_name: str,
                 context: BgmContext, env: Environment) -> None:
        super().__init__(scope, construct_id, stack_name=stack_name, env=env)
        self.context: BgmContext = context
        self.projectDirectory: pathlib.Path = pathlib.Path(__file__).parent
        DbConstruct(self, id=context.logicalIdFor('db'), context=context)
        self.api = APIConstruct(self, id=context.logicalIdFor('api'), context=context)
        self.web = WebConstruct(self, id=context.logicalIdFor('web'), context=context)
        self.distribution = DistributionConstruct(
            self, id=context.logicalIdFor('distro'),
            context=context, bucket=self.web.website_bucket, api=self.api.restApi)
        self.web.deployWebSite(distribution=self.distribution.distribution, context=context)

    # Get rid of those appended hashes that ensure that no two logical IDs conflict. They make output keys
    # hard to predict and clutter things up. If I fuck up and produce conflicts, the build will tell me.
    def _allocate_logical_id(self, cfn_element):
        return super()._allocate_logical_id(cfn_element)[:-8]


app: App = App()
envName = app.node.try_get_context('ENV')
# Avoid accidentally deploying anywhere if the environment has not been explicitly passed via --context ENV=xxxx
if not envName:
    print('ENV must be explicitly passed via `--context ENV=xxxx`', file=sys.stderr)
    sys.exit(-1)

webPackage = f'bgm-nerdrock-{envName}-web.zip'
lambdaPackage = f'bgm-nerdrock-{envName}-lambdas.zip'
context: BgmContext = BgmContext(envName, webPackage, lambdaPackage)
for tag, val in context.getTags().items():
    Tags.of(app).add(tag, val)

stack = CdkStack(app, context.logicalIdFor('stack'), context.physicalIdFor('stack'), context,
                 env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
