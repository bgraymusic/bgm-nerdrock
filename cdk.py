#!/usr/bin/env python3

from typing import List
import yaml

from aws_cdk import App
from git.repo.base import Repo

from cdk.bgm_stack import GlobalStack, ProdEnvStack, NonProdEnvStack
from cdk.bgm_context import GlobalContext, EnvContext


# Load configuration file
with open('cdk/cdk_config.yml') as config_file:
    config: dict = yaml.load(config_file.read(), Loader=yaml.BaseLoader)

# Create CDK app
app: App = App()

# Read in ENV from cmdLine context and create our list of stacks
envFromCmdLine = app.node.try_get_context('ENV')
if envFromCmdLine == 'global':
    environments: List[str] = []
elif envFromCmdLine:                              # only the one specified environment
    environments: List[str] = [envFromCmdLine]
else:                                           # prod colors (NOT 'prod'), staging, and all branches
    environments: List[str] = config['ssm-parameters']['prod-deployment-colors'].copy()
    environments.append('staging')
    repo = Repo()
    for branch in repo.branches:
        if branch.name != 'trunk':
            environments.append(branch.name)

# Synthesize the global stack, followed by any environments to be processed in this run
globalStack = GlobalStack(app, GlobalContext(config), config['ssm-parameters'], config['key-value-pairs'])
stacks = [globalStack.stack_name]
for env in environments:
    envContext = EnvContext(env, config)
    envStack = (ProdEnvStack(app, envContext, globalStack)
                if envContext.isProd
                else NonProdEnvStack(app, envContext, globalStack))
    stacks.append(envStack.stack_name)
app.synth()

# Write out all stacks we just synthesized, because the output of `cdk deploy` – which contains this info – for some
# reason cannot be captured in GitHub actions
with open('stacks.yml', 'w') as f:
    yaml.dump(stacks, f)
