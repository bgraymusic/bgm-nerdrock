import boto3
import deepmerge
import json
import os
import yaml


def init_config(LOG):
    with open(os.getenv('config', 'config.yml')) as public_config_file:
        config_contents = public_config_file.read()
        public_config = yaml.load(config_contents, Loader=yaml.BaseLoader)
    secret_config_bucket = os.getenv('secretsBucket', None)
    secret_config_file = os.getenv('secretsFile', 'secrets.yml')
    if secret_config_bucket is not None:
        s3_client = boto3.client('s3')
        s3_obj = s3_client.get_object(
            Bucket=secret_config_bucket, Key=secret_config_file)
        secret_config = yaml.load(s3_obj['Body'], Loader=yaml.BaseLoader)
    else:
        with open(secret_config_file) as secret_config_file:
            secret_config = yaml.load(
                secret_config_file.read(), Loader=yaml.BaseLoader)
    final_config = deepmerge.always_merger.merge(public_config, secret_config)
    LOG.debug(f'final config: {json.dumps(final_config)}')
    return final_config
