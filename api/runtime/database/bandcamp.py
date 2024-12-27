from decimal import Decimal
import json
import requests
from requests import Response
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

    def execute_bc_api(self, path, payload):
        response: Response = requests.get(Config.get()['bandcamp']['bcApiUrl'] + path, payload)
        response.raise_for_status()
        return json.loads(response.text, parse_float=Decimal)
