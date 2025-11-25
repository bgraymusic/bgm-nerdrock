"""Object representation of the cdk_config.yml file"""

from __future__ import annotations
import typing
import yaml


class CdkConfig(yaml.YAMLObject):
    """Object representation of the CDK config file"""

    __slots__ = ('context', 'ssm_parameters', 'key_value_pairs')
    file_path: str = 'cdk/cdk_config.yml'
    yaml_tag: str = '!CdkConfig'
    yaml_loader = yaml.SafeLoader

    _instance: typing.Self | None = None

    @staticmethod
    def constructor(loader, node):
        value = loader.construct_mapping(node)
        return CdkConfig(**value)

    @classmethod
    def get(cls) -> typing.Self:
        if cls._instance is None:
            with open(cls.file_path, encoding='utf-8') as config_file:
                cls._instance = yaml.load(config_file.read(), Loader=CdkConfigLoader)

        assert cls._instance is not None
        return cls._instance


    def __init__(self, context: CdkContext, ssm_parameters: CdkSsmParameters, key_value_pairs: CdkKeyValuePairs) -> None:
        self.context = context
        self.ssm_parameters = ssm_parameters
        self.key_value_pairs = key_value_pairs


# yaml.add_path_resolver(CdkConfig.yaml_tag, [CdkConfig.__name__], dict)


class CdkContext(yaml.YAMLObject):
    """Object representation of the cdk_config.yml file"""

    __slots__ = ('org', 'project', 'domain', 'blog_hostname', 'blog_target_domain', 'secrets_file', 'check_ip_url',
                 'allow_ip_key', 'assets_dir', 'non_prod_func_source_file', 'prod_func_source_file')
    yaml_tag = '!CdkContext'

    @staticmethod
    def constructor(loader, node):
        value = loader.construct_mapping(node)
        return CdkContext(**value)

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


# yaml.add_path_resolver(CdkContext.yaml_tag, [CdkContext.__name__], dict)


class CdkSsmParameters(yaml.YAMLObject):
    # No slots because we want to access this as an object AND dict (via vars())
    # __slots__ = ('prod_deployment_colors', 'active_prod_color', 'secrets_bucket')
    yaml_tag = '!CdkSsmParameters'

    @staticmethod
    def constructor(loader, node):
        value = loader.construct_mapping(node)
        return CdkSsmParameters(**value)

    def __init__(self, prod_deployment_colors: list[str], active_prod_color: str, secrets_bucket: str) -> None:
        self.prod_deployment_colors = prod_deployment_colors
        self.active_prod_color = active_prod_color
        self.secrets_bucket = secrets_bucket


# yaml.add_path_resolver(CdkSsmParameters.yaml_tag, [CdkSsmParameters.__name__], dict)


class CdkKeyValuePairs(yaml.YAMLObject):
    # No slots because we want to access this as an object AND dict (via vars())
    # __slots__ = ('allowed_ip', 'redirect_domain')
    yaml_tag = '!CdkKeyValuePairs'

    @staticmethod
    def constructor(loader, node):
        value = loader.construct_mapping(node)
        return CdkKeyValuePairs(**value)

    def __init__(self, allowed_ip: str, redirect_domain: str) -> None:
        self.allowed_ip = allowed_ip
        self.redirect_domain = redirect_domain


# yaml.add_path_resolver(CdkKeyValuePairs.yaml_tag, [CdkKeyValuePairs.__name__], dict)


class CdkConfigLoader(yaml.SafeLoader):
    pass


CdkConfigLoader.add_constructor(CdkConfig.yaml_tag, CdkConfig.constructor)
CdkConfigLoader.add_constructor(CdkContext.yaml_tag, CdkContext.constructor)
CdkConfigLoader.add_constructor(CdkSsmParameters.yaml_tag, CdkSsmParameters.constructor)
CdkConfigLoader.add_constructor(CdkKeyValuePairs.yaml_tag, CdkKeyValuePairs.constructor)
