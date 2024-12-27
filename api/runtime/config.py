import os
import json
import boto3.s3
import yaml
import pathlib
import boto3
import deepmerge
from .log import Log


class Config:
    __instance = None

    def __init__(self):
        LOG = Log.get()

        with open(os.getenv('config', f'{pathlib.Path(__file__).parent.parent}/config.yml')) as public_config_file:
            config_contents = public_config_file.read()
            public_config = yaml.load(config_contents, Loader=yaml.BaseLoader)
        secret_config_bucket = os.getenv('secretsBucket', None)
        secret_config_file = os.getenv('secretsFile', f'{pathlib.Path(__file__).parent.parent}/local/secrets.yml')
        if secret_config_bucket is not None:
            s3_client = boto3.client('s3')
            s3_obj = s3_client.get_object(
                Bucket=secret_config_bucket, Key=secret_config_file)
            secret_config = yaml.load(s3_obj['Body'], Loader=yaml.BaseLoader)
        else:
            with open(secret_config_file) as secret_config_file:
                secret_config = yaml.load(
                    secret_config_file.read(), Loader=yaml.BaseLoader)
        self.final_config = deepmerge.always_merger.merge(public_config, secret_config)
        LOG.debug(f'final config: {json.dumps(self.final_config)}')

    @classmethod
    def get(cls, force_new=False):
        if not Config.__instance or force_new:
            Config.__instance = Config()
        return Config.__instance.final_config
