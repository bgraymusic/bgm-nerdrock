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
    def __init__(self, scope: Construct, construct_id: str, context: BgmContext, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.context: BgmContext = context
        self.projectDirectory: pathlib.Path = pathlib.Path(__file__).parent
        DbConstruct(self, id=context.logicalIdFor('db'), context=context)
        api = APIConstruct(self, id=context.logicalIdFor('api'), context=context)
        web = WebConstruct(self, id=context.logicalIdFor('web'), context=context)
        distribution = DistributionConstruct(
            self, id=context.logicalIdFor('distro'),
            stage=context.stage, bucket=web.website_bucket, api=api.restApi)
        web.deployWebSite(distribution=distribution.distribution)


app = App()
stage = app.node.try_get_context('stage')
# Avoid accidentally deploying anywhere if stage has not been explicitly passed via --context stage=xxxx
if not stage:
    print('Stage must be explicitly passed via `--context stage=xxxx`', file=sys.stderr)
    sys.exit(-1)

context: BgmContext = BgmContext(stage)
for tag, val in context.getTags().items():
    Tags.of(app).add(tag, val)

CdkStack(app, context.logicalIdFor('stack'), context,
         env=Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')))

app.synth()
