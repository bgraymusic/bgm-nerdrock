"""Object representation of the config.yml file"""

from __future__ import annotations
import json
import os
import pathlib
import typing
import yaml

import boto3
import mypy_boto3_s3 as boto3_s3
import deepmerge

from api.runtime.log import Log


DEFAULT_CONFIG_PATH = f'{pathlib.Path(__file__).parent.parent}/config.yml'
DEFAULT_SECRETS_PATH = f'{pathlib.Path(__file__).parent.parent}/local/secrets.yml'


class Config:
    """Object representation of the config.yml file"""

    _instance = None

    def __init__(self) -> None:
        with open(
            os.getenv('config', DEFAULT_CONFIG_PATH), encoding='utf-8'
        ) as public_config_file:
            config_contents = public_config_file.read()
            public_config = yaml.load(config_contents, Loader=yaml.BaseLoader)
        secret_config_bucket = os.getenv('secretsBucket', None)
        secret_config_file = os.getenv('secretsFile', DEFAULT_SECRETS_PATH)
        if secret_config_bucket is not None:
            s3_client: boto3_s3.S3Client = boto3.client('s3')
            s3_obj = s3_client.get_object(
                Bucket=secret_config_bucket, Key=secret_config_file)
            secret_config = yaml.load(s3_obj['Body'], Loader=yaml.BaseLoader)
        else:
            with open(secret_config_file, encoding='utf-8') as secret_config_file:
                secret_config = yaml.load(
                    secret_config_file.read(), Loader=yaml.BaseLoader)
        final_config = deepmerge.always_merger.merge(public_config, secret_config)
        Log.get().debug(f'final config: {json.dumps(final_config)}')
        self.populate(final_config)

    def populate(self, config: dict[str, typing.Any]) -> None:
        self.aws = AWSConfig(config['aws'])
        self.bandcamp = BandcampConfig(config['bandcamp'])
        self.albums = AlbumsConfig(config['albums'])
        self.badges = BadgesConfig(config['badges'])

    @classmethod
    def get(cls, force_new=False) -> Config:
        if not Config._instance or force_new:
            Config._instance = Config()
        return Config._instance


class AWSConfig:
    def __init__(self, config: dict[str, typing.Any]) -> None:
        self.account: str = config['account']
        self.role: str = config['role']
        self.region: str = config['region']
        self.album_table: str = config['album_table']
        self.track_table: str = config['track_table']


class BandcampConfig:
    def __init__(self, config: dict[str, typing.Any]) -> None:
        self.bc_api_url: str = config['bc_api_url']
        self.bc_key: str = config['bc_key']
        self.bc_discography_path: str = config['bc_discography_path']
        self.bc_album_path: str = config['bc_album_path']
        self.bc_track_path: str = config['bc_track_path']
        self.bc_band_ids: list[int] = config['bc_band_ids']


class AlbumsConfig:
    def __init__(self, config: dict[str, typing.Any]) -> None:
        self.forward_sorted: list[int] = config['forward_sorted']


class BadgesConfig:
    def __init__(self, config: dict[str, typing.Any]) -> None:
        self.encryption_key: str = config['encryption_key']
        self.default_album_ids: list[int] = config['default_album_ids']
        self.badges: dict[str, Badge] = {b: Badge(config['badges'][b]) for b in config['badges']}


class Badge:
    def __init__(self, config: dict[str, typing.Any]) -> None:
        self.code: str = config['code']
        self.key: str = config['key']
        self.enum: str = config['enum']
        self.album_ids: list[int] = config['album_ids']
