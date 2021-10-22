from functools import reduce
import yaml
from database import Bandcamp, DecimalLoader


class DatabaseService:

    def __init__(self, config, LOG, album_table, track_table, bandcamp=None):
        self.config = config
        self.LOG = LOG
        self.album_table = album_table
        self.track_table = track_table
        self.bandcamp = bandcamp if bandcamp else Bandcamp(config, LOG)

        with open('database/track_info.yml') as track_info_config_file:
            config_contents = track_info_config_file.read()
            self.track_info = yaml.load(config_contents, Loader=DecimalLoader)

        self.album_ids = set()
        for album_id in self.config['badges']['defaultAlbumIDs']:
            self.album_ids.add(album_id)
        self.album_ids.update(set(reduce(lambda left, right: left + right['albumIDs'], self.config['badges']['badges'].values(), [])))

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

    # TODO: Use trackInfo when present (JSON string data? file upload?), defaulting to filesystem track_info.yml when None
    def populate(self, track_info=None):
        with self.album_table.batch_writer() as album_batch:
            for album_id in self.album_ids:
                album_data = self.bandcamp.get_album_from_bc(album_id)
                album_batch.put_item(Item=album_data)

                for track in album_data['tracks']:
                    if track['track_id'] in self.track_info:
                        info = self.track_info[track['track_id']]
                        track.update(info)


                with self.track_table.batch_writer() as track_batch:
                    for track in album_data['tracks']:
                        track_batch.put_item(Item=track)

                album_data.pop('tracks')
                self.album_table.put_item(Item=album_data)
