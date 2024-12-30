import os
from functools import reduce
import pathlib
import yaml
import boto3
from boto3.dynamodb.table import TableResource
from boto3.dynamodb.conditions import Key
from ..config import Config
from .bandcamp import Bandcamp
from .decimal_yaml import DecimalLoader


class DatabaseService:

    def __init__(self, *,
                 album_table: TableResource = None,
                 track_table: TableResource = None,
                 bandcamp: Bandcamp = None):
        self.album_table = album_table if album_table else \
            boto3.resource('dynamodb').Table(f'{os.getenv("tablePrefix")}-{Config.get()["aws"]["albumTable"]}')
        self.track_table = track_table if track_table else \
            boto3.resource('dynamodb').Table(f'{os.getenv("tablePrefix")}-{Config.get()["aws"]["trackTable"]}')
        self.bandcamp = bandcamp if bandcamp else Bandcamp()

        with open(os.getenv('trackInfo', f'{pathlib.Path(__file__).parent}/track_info.yml')) as track_info_config_file:
            config_contents = track_info_config_file.read()
            self.track_info = yaml.load(config_contents, Loader=DecimalLoader)

        self.album_ids = set()
        for album_id in Config.get()['badges']['defaultAlbumIDs']:
            self.album_ids.add(album_id)
        self.album_ids.update(set(reduce(lambda left,
                                         right: left + right['albumIDs'],
                                         Config.get()['badges']['badges'].values(),
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
    def populate(self, track_info=None):
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

    def queryAlbum(self, album_id: int):
        return self.album_table.get_item(Key={'album_id': album_id})['Item']

    def queryTracksFromAlbum(self, album_id: int, forward_sorted: bool):
        return self.track_table.query(
            KeyConditionExpression=Key('album_id').eq(album_id),
            ScanIndexForward=forward_sorted
        )['Items']
