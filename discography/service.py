import boto3


class DiscographyService:

    def __init__(self, config, LOG, album_table, track_table, badge_core):
        self.config = config
        self.LOG = LOG
        self.badge_core = badge_core
        self.album_table = album_table
        self.track_table = track_table

    def get_discography(self, badges):
        album_ids = self.get_album_ids_for_badges(badges)
        self.LOG.debug(f'Fetching discography for albums: {album_ids}')
        return self.get_selected_albums(album_ids)

    def get_selected_albums(self, album_ids):
        albums = []
        for album_id in album_ids:
            album = self.album_table.get_item(Key={'album_id': int(album_id)})['Item']
            forwardSorted = album_id in self.config['albums']['forwardSorted']
            tracks = self.track_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('album_id').eq(int(album_id)),
                ScanIndexForward = album_id in self.config['albums']['forwardSorted']
            )['Items']
            album['tracks'] = tracks
            albums.append(album)
        return albums

    def get_album_ids_for_badges(self, badges):
        album_ids = self.config['badges']['defaultAlbumIDs'].copy()
        for badge_key in badges:
            spec = self.badge_core.badges_spec[badge_key]
            if spec and 'albumIDs' in spec:
                album_ids += spec['albumIDs']
        return album_ids
