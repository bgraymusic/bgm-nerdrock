#!/usr/bin/env python3

import yaml

from aws_cdk import App
from git.repo.base import Repo

from cdk.bgm_stack import GlobalStack, ProdEnvStack, NonProdEnvStack
from cdk.bgm_context import GlobalContext, EnvContext


def create_app() -> App:
    return App()


def load_config() -> dict:
    with open('cdk/cdk_config.yml') as config_file:
        return yaml.load(config_file.read(), Loader=yaml.BaseLoader)


def create_environment_list(app, config):
    envFromCmdLine = app.node.try_get_context('ENV')
    if envFromCmdLine == 'global':
        environments: list[str] = []
    elif envFromCmdLine:                              # only the one specified environment
        environments: list[str] = [envFromCmdLine]
    else:                                           # prod colors (NOT 'prod'), staging, and all branches
        environments: list[str] = config['ssm-parameters']['prod-deployment-colors'].copy()
        environments.append('staging')
        repo = Repo()
        for branch in repo.branches:
            if branch.name != 'trunk':
                environments.append(branch.name)
    return environments


def create_stacks(app, config, environments):
    globalStack = GlobalStack(app, GlobalContext(config), config['ssm-parameters'], config['key-value-pairs'])
    for env in environments:
        envContext = EnvContext(env, config)
        (ProdEnvStack(app, envContext, globalStack)
         if envContext.isProd
         else NonProdEnvStack(app, envContext, globalStack))


def dump_stacks(stacks: list[str]):
    '''Write out all stacks we just synthesized'''

    print(f'Stacks: {stacks}')
    with open('stacks.yml', 'w') as f:
        yaml.dump(stacks, f)


app = create_app()
config = load_config()
environments = create_environment_list(app, config)
create_stacks(app, config, environments)
assembly = app.synth()
dump_stacks([x.stack_name for x in assembly.stacks])
