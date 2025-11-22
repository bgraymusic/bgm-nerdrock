"""Object representation of the cdk_config.yml file"""

from __future__ import annotations
import typing
import yaml


class BgmConfig(yaml.YAMLObject):
    """Object representation of the CDK config file"""

    __slots__ = ('context', 'ssm_parameters', 'key_value_pairs')
    file_path: str = 'cdk/cdk_config.yml'
    yaml_tag: str = '!Config'
    _instance: typing.Self | None = None

    @classmethod
    def get(cls) -> typing.Self:
        if cls._instance is None:
            with open(cls.file_path, encoding='utf-8') as config_file:
                cls._instance = yaml.safe_load(config_file.read())

        assert cls._instance is not None
        return cls._instance


    def __init__(self, context: Context, ssm_parameters: SsmParameters, key_value_pairs: KeyValuePairs) -> None:
        self.context = context
        self.ssm_parameters = ssm_parameters
        self.key_value_pairs = key_value_pairs


class Context(yaml.YAMLObject):
    """Object representation of the cdk_config.yml file"""

    __slots__ = ('org', 'project', 'domain', 'blog_hostname', 'blog_target_domain', 'secrets_file', 'check_ip_url',
                 'allow_ip_key', 'assets_dir', 'non_prod_func_source_file', 'prod_func_source_file')
    yaml_tag = '!Context'

    def __init__(
        self, org: str, project: str, domain: str, blog_hostname: str, blog_target_domain: str,
        secrets_file: str, check_ip_url: str, allow_ip_key: str, assets_dir: str,
        non_prod_func_source_file: str, prod_func_source_file: str
    ) -> None:
        self.org = org
        self.project = project
        self.domain = domain
        self.blog_hostname = blog_hostname
        self.blog_target_domain = blog_target_domain
        self.secrets_file = secrets_file
        self.check_ip_url = check_ip_url
        self.allow_ip_key = allow_ip_key
        self.assets_dir = assets_dir
        self.non_prod_func_source_file = non_prod_func_source_file
        self.prod_func_source_file = prod_func_source_file


class SsmParameters(yaml.YAMLObject):
    __slots__ = ('prod_deployment_colors', 'active_prod_color', 'secrets_bucket')
    yaml_tag = '!SsmParamaters'

    def __init__(self, prod_deployment_colors: list[str], active_prod_color: str, secrets_bucket: str) -> None:
        self.prod_deployment_colors = prod_deployment_colors
        self.active_prod_color = active_prod_color
        self.secrets_bucket = secrets_bucket


class KeyValuePairs(yaml.YAMLObject):
    __slots__ = ('allowed_ip', 'redirect_domain')
    yaml_tag = '!KeyValuePairs'

    def __init__(self, allowed_ip: str, redirect_domain: str) -> None:
        self.allowed_ip = allowed_ip
        self.redirect_domain = redirect_domain
