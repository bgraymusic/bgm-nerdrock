"""Non-boundary implementation of the database service"""

import os
from functools import reduce
import pathlib
import typing
import yaml

import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3_dynamodb import type_defs as boto3_db_types
from mypy_boto3_dynamodb.service_resource import Table as TableResource

from api.runtime.config import Config
from api.runtime.database.bandcamp import Bandcamp
from api.runtime.database.decimal_yaml import DecimalLoader


class DatabaseService:
    """Non-boundary implementation of the database service"""

    def __init__(self, *,
                 album_table: TableResource | None = None,
                 track_table: TableResource | None = None,
                 bandcamp: Bandcamp | None = None):
        self.album_table: TableResource = album_table if album_table else (
            boto3.resource('dynamodb').Table(f'{os.getenv('tablePrefix')}-{Config.get().aws.album_table}')
        )
        self.track_table = track_table if track_table else \
            boto3.resource('dynamodb').Table(f'{os.getenv('tablePrefix')}-{Config.get().aws.track_table}')
        self.bandcamp = bandcamp if bandcamp else Bandcamp()

        with open(
            os.getenv('trackInfo', f'{pathlib.Path(__file__).parent}/track_info.yml'), encoding='utf-8'
        ) as track_info_config_file:
            config_contents = track_info_config_file.read()
            self.track_info = yaml.load(config_contents, Loader=typing.cast(type[yaml.SafeLoader], DecimalLoader))

        self.album_ids = set()
        for album_id in Config.get().badges.default_album_ids:
            self.album_ids.add(album_id)
        self.album_ids.update(set(reduce(lambda left,
                                         right: left + right.album_ids,
                                         Config.get().badges.badges.values(),
                                         [])))

    def clear(self):
        with self.album_table.batch_writer() as album_batch:
            albums = self.album_table.scan(ProjectionExpression='album_id')['Items']
            for album in albums:
                album_batch.delete_item(Key={'album_id': album['album_id']})
        with self.track_table.batch_writer() as track_batch:
            tracks = self.track_table.scan(
                ProjectionExpression='album_id, #n',
                ExpressionAttributeNames={'#n': 'number'}
            )['Items']
            for track in tracks:
                track_batch.delete_item(Key={'album_id': track['album_id'], 'number': track['number']})

    # TODO: Use trackInfo when present (JSON string data? file upload?),
    #       defaulting to filesystem track_info.yml when None
    # def populate(self, track_info=None) -> int:
    def populate(self) -> int:
        with self.album_table.batch_writer() as album_batch:
            for album_id in self.album_ids:
                album_data = self.bandcamp.get_album_from_bc(album_id)
                album_batch.put_item(Item=album_data)

                for track in album_data['tracks']:
                    if track['track_id'] in self.track_info:
                        track.update(self.track_info[track['track_id']])

                with self.track_table.batch_writer() as track_batch:
                    for track in album_data['tracks']:
                        track_batch.put_item(Item=track)

                self.album_table.put_item(Item=album_data.copy())
        return len(self.album_ids)

    def query_album(self, album_id: int) -> dict[str, boto3_db_types.TableAttributeValueTypeDef]:
        return self.album_table.get_item(Key={'album_id': album_id}).get('Item') or {}

    def query_tracks_from_album(
        self, album_id: int, forward_sorted: bool
    ) -> list[dict[str, boto3_db_types.TableAttributeValueTypeDef]]:
        return self.track_table.query(
            KeyConditionExpression=Key('album_id').eq(album_id),
            ScanIndexForward=forward_sorted
        )['Items'] or []
