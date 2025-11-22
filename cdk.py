#!/usr/bin/env python3

"""The top-level entry point to the NerdRock CDK app

This app is written in such a way that it can produce configurable stacks
based on the ENV variables sent into the cdk CLI. A global environment spans
all others, and updates to it must be made judiciously and carefully. All
other environments are categorized as "prod-like" or not. Prod environments
(BLUE & GREEN) and staging are prod-like and include more expensive tooling.
All others are functionally complete but may sacrifice scalability, redundancy,
etc.

Examples:

    cdk deploy --all -c ENV=prod -- deploy production and flip GREEN/BLUE
    cdk deploy --all -c ENV=staging -- deploy staging
    cdk deploy --all -c ENV=feature/foo -- deploy environment for git branch
    cdk deploy --all -c ENV=global -- deploy only the global environment
"""

import yaml

import aws_cdk
import git.repo.base as git

from cdk import bgm_config, bgm_context, bgm_stack


def create_app() -> aws_cdk.App:
    return aws_cdk.App()


def create_environment_list(
    app: aws_cdk.App, config: bgm_config.BgmConfig
) -> list[str]:
    """Returns a list of environments to generate based on '-c' env var"""
    env_from_cmd_line = app.node.try_get_context('ENV')
    if env_from_cmd_line == 'global':
        environments: list[str] = []
    elif env_from_cmd_line:  # only the one specified environment
        environments: list[str] = [env_from_cmd_line]
    else:  # prod colors (NOT 'prod'), staging, and all branches
        environments: list[str] = config.ssm_parameters.prod_deployment_colors.copy()
        environments.append('staging')
        repo = git.Repo()
        for branch in repo.branches:
            if branch.name != 'trunk':
                environments.append(branch.name)
    return environments


def create_stacks(app: aws_cdk.App, config: bgm_config.BgmConfig, environments: list[str]) -> None:
    global_stack = bgm_stack.GlobalStack(app, bgm_context.GlobalContext(config), config)

    for env in environments:
        env_context = bgm_context.EnvContext(env, config)
        if env_context.is_prod:
            bgm_stack.ProdEnvStack(app, env_context, global_stack)
        else:
            bgm_stack.NonProdEnvStack(app, env_context, global_stack)


def dump_stacks(stacks: list[str]) -> None:
    """Writes out all stacks we just synthesized"""

    print(f'Stacks: {stacks}')
    with open('stacks.yml', 'w', encoding='utf-8') as f:
        yaml.dump(stacks, f)


cdk_app: aws_cdk.App = create_app()
cdk_environments: list[str] = create_environment_list(cdk_app, bgm_config.BgmConfig.get())
create_stacks(cdk_app, bgm_config.BgmConfig.get(), cdk_environments)
cdk_assembly: aws_cdk.cx_api.CloudAssembly = cdk_app.synth()
dump_stacks([x.stack_name for x in cdk_assembly.stacks])
