import requests


class Bandcamp:

    def __init__(self, config, LOG):
        self.config = config
        self.bc_key_param = {'key': config['bandcamp']['bcKey']}
        self.LOG = LOG

    def get_band_from_bc(self, band_id):
        payload = {**self.bc_key_param, **{'band_id': band_id}}
        return self.execute_bc_api(self.config['bandcamp']['bcDiscographyPath'], payload)

    def get_album_from_bc(self, album_id):
        payload = {**self.bc_key_param, **{'album_id': album_id}}
        return self.execute_bc_api(self.config['bandcamp']['bcAlbumPath'], payload)

    def get_track_from_bc(self, track_id):
        payload = {**self.bc_key_param, **{'track_id': track_id}}
        return self.execute_bc_api(self.config['bandcamp']['bcTrackPath'], payload)

    def execute_bc_api(self, path, payload):
        response = requests.get(
            self.config['bandcamp']['bcApiUrl'] + path, payload)
        response.raise_for_status()
        return response.json()
