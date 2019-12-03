import requests


class Bandcamp:

    def __init__(self, config, LOG):
        self.config = config
        self.bc_key_param = {'key': config['bandcamp']['bcKey']}
        self.LOG = LOG

    def get_band_from_bc(self, band_id):
        payload = {**self.bc_key_param, **{'band_id': band_id}}
        band = requests.get(self.config['bandcamp']['bcApiUrl'] +
                            self.config['bandcamp']['bcDiscographyPath'], payload).json()
        return band

    def get_album_from_bc(self, album_id):
        payload = {**self.bc_key_param, **{'album_id': album_id}}
        album = requests.get(self.config['bandcamp']['bcApiUrl'] +
                             self.config['bandcamp']['bcAlbumPath'], payload).json()
        for track in album['tracks']:
            track.update(self.get_track_from_bc(track['track_id']))
        return album

    def get_track_from_bc(self, track_id):
        payload = {**self.bc_key_param, **{'track_id': track_id}}
        track = requests.get(self.config['bandcamp']['bcApiUrl'] +
                             self.config['bandcamp']['bcTrackPath'], payload).json()
        return track
