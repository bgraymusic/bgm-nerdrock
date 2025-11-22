"""Utility class to fetch data from the Bandcamp API"""

from decimal import Decimal
import json
import urllib.request
from ..config import Config


class Bandcamp:
    """Utility class to fetch data from the Bandcamp API"""

    def get_band_from_bc(self, band_id) -> dict:
        payload = {**{'key': Config.get().bandcamp.bc_key}, **{'band_id': band_id}}
        return self.execute_bc_api(Config.get().bandcamp.bc_discography_path, payload)

    def get_album_from_bc(self, album_id) -> dict:
        payload = {**{'key': Config.get().bandcamp.bc_key}, **{'band_id': album_id}}
        return self.execute_bc_api(Config.get().bandcamp.bc_album_path, payload)

    def get_track_from_bc(self, track_id) -> dict:
        payload = {**{'key': Config.get().bandcamp.bc_key}, **{'track_id': track_id}}
        return self.execute_bc_api(Config.get().bandcamp.bc_track_path, payload)

    def execute_bc_api(self, path, payload: dict) -> dict:
        url = f'{Config.get().bandcamp.bc_api_url}{path}?'
        for key, value in payload.items():
            url = f'{url}{key}={value}&'
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode('utf-8'), parse_float=Decimal)
