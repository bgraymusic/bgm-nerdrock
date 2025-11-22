"""Portable data for use by stacks and constructs"""

import abc
import pathlib
import re

import boto3
from mypy_boto3_ssm import type_defs
import botocore.exceptions

from cdk import bgm_config


class BgmContext(abc.ABC):
    """Context base class, with common data and operations"""

    def __init__(self, config: bgm_config.BgmConfig):
        self.project_directory: pathlib.Path = pathlib.Path(__file__).parent.parent
        self.cdk_directory: pathlib.Path = pathlib.Path(__file__).parent

        self.org: str = ''
        self.project: str = ''
        self.domain: str = ''
        self.blog_host_name: str = ''
        self.blog_target_domain: str = ''
        self.secrets_file: str = ''
        self.check_ip_url: str = ''
        self.allow_ip_key: str = ''
        self.assets_dir: str = ''
        self.non_prod_func_source_file: str = ''
        self.prod_func_source_file: str = ''

        for key, value in vars(config.context):
            setattr(self, key, value)

    @abc.abstractmethod
    def logical_id_for(self, construct_id: str) -> str:
        pass

    @abc.abstractmethod
    def physical_id_for(self, construct_id: str) -> str:
        pass

    @abc.abstractmethod
    def get_stack_description(self) -> str:
        pass

    def get_tags(self) -> dict[str, str]:
        return {'org': self.org, 'project': self.project}

    def capitalize(self, s: str) -> str:
        s = re.sub(r'[\W]', '', s)
        return re.sub('([a-zA-Z])', lambda x: x.groups()[0].upper(), s, 1)


class GlobalContext(BgmContext):
    """Context class for the global stack"""

    def __init__(self, config: bgm_config.BgmConfig):
        super().__init__(config)

        self.prod_func_path = f'{self.cdk_directory}/{self.prod_func_source_file}'

        self.logical_id_prefix = ''.join([self.capitalize(x) for x in [self.org, self.project, 'global']])
        self.physical_id_prefix = f'{self.org.lower()}-{self.project.lower()}-global'

    def logical_id_for(self, construct_id: str) -> str:
        return f'{self.logical_id_prefix}{''.join([self.capitalize(x) for x in construct_id.split('-')])}'

    def physical_id_for(self, construct_id: str) -> str:
        return f'{self.physical_id_prefix}-{construct_id}'

    def get_stack_description(self) -> str:
        return 'The global stack for all NerdRock environments to reference'

    def get_tags(self) -> dict[str, str]:
        tags = super().get_tags()
        tags['app'] = self.physical_id_prefix
        return tags


class EnvContext(BgmContext):
    """Context class for all environment (non-global) stacks"""

    def __init__(self, env: str, config: bgm_config.BgmConfig):
        super().__init__(config)

        self.env = self.normalize_env_name(env)
        self.lambda_package = f'./{self.assets_dir}/{self.org.lower()}-{self.project.lower()}-{self.env}-lambdas.zip'
        self.web_package = f'./{self.assets_dir}/{self.org.lower()}-{self.project.lower()}-{self.env}-web.zip'
        self.non_prod_func_path = f'{self.cdk_directory}/{self.non_prod_func_source_file}'
        self.prod_func_path = f'{self.cdk_directory}/{self.prod_func_source_file}'

        self.default_prod_color = config.ssm_parameters.active_prod_color
        self.figure_if_is_prod(config.ssm_parameters.prod_deployment_colors.copy())

        self.logical_id_prefix = ''.join([self.capitalize(x) for x in [self.org, self.project, self.env]])
        self.physical_id_prefix = f'{self.org.lower()}-{self.project.lower()}-{self.env}'
        self.host_name = f'{self.env.lower()}.{self.domain}'

    def normalize_env_name(self, env: str) -> str:
        env = re.sub('[^A-Za-z0-9-]+', '-', env)
        env = re.sub('^[-]', '', env)
        env = re.sub('[-]$', '', env)
        return env

    def figure_if_is_prod(self, prod_colors: list[str]) -> None:
        ssm = boto3.client('ssm')
        if self.env == 'staging':
            self.is_prod = True
        elif self.env == 'prod':
            self.is_prod = True
            try:
                prod_color_result: type_defs.GetParameterResultTypeDef = ssm.get_parameter(
                    Name='bgm-nerdrock-active-prod-color'
                )
                self.env = self.get_next_prod_color(prod_color_result.get('Parameter').get('Value'), prod_colors) \
                    or self.default_prod_color
            except botocore.exceptions.ClientError:
                self.env = self.default_prod_color
        elif self.env.upper() in [x.upper() for x in prod_colors]:
            self.is_prod = True
        else:
            self.is_prod = False

    def get_next_prod_color(self, prod_color: str | None, prod_colors: list[str]) -> str:
        if not prod_color or prod_color == prod_colors[-1]:
            return prod_colors[0]
        else:
            return prod_colors[prod_colors.index(prod_color)+1]

    def logical_id_for(self, construct_id: str) -> str:
        return f'{self.logical_id_prefix}{''.join([self.capitalize(x) for x in construct_id.split('-')])}'

    def physical_id_for(self, construct_id: str) -> str:
        return f'{self.physical_id_prefix}-{construct_id}'

    def get_stack_description(self) -> str:
        if self.env == 'staging':
            return 'Nerdrock production-like staging environment'
        elif self.is_prod:
            return f'Nerdrock {self.env} production environment'
        else:
            return f'Nerdrock {self.env} lower environment'

    def get_tags(self) -> dict[str, str]:
        tags = super().get_tags()
        tags['env'] = self.env
        tags['app'] = self.physical_id_prefix
        return tags
