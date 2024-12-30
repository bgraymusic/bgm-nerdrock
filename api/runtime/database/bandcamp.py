from decimal import Decimal
import json
import urllib.request
from ..config import Config


class Bandcamp:

    def get_band_from_bc(self, band_id):
        payload = {**{'key': Config.get()['bandcamp']['bcKey']}, **{'band_id': band_id}}
        return self.execute_bc_api(Config.get()['bandcamp']['bcDiscographyPath'], payload)

    def get_album_from_bc(self, album_id):
        payload = {**{'key': Config.get()['bandcamp']['bcKey']}, **{'album_id': album_id}}
        return self.execute_bc_api(Config.get()['bandcamp']['bcAlbumPath'], payload)

    def get_track_from_bc(self, track_id):
        payload = {**{'key': Config.get()['bandcamp']['bcKey']}, **{'track_id': track_id}}
        return self.execute_bc_api(Config.get()['bandcamp']['bcTrackPath'], payload)

    def execute_bc_api(self, path, payload: dict):
        url = f'{Config.get()['bandcamp']['bcApiUrl']}{path}?'
        for key, value in payload.items():
            url = f'{url}{key}={value}&'
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'), parse_float=Decimal)
