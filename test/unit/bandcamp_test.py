from database import *
from http import HTTPStatus
import json
import logging
import requests
from requests.exceptions import HTTPError
import responses
import unittest


class BandcampTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = {
            'bandcamp': {
                'bcKey': 'asdfghjkl',
                'bcBandIDs': [230945364],
                'bcApiUrl': 'http://api.bandcamp.com/api',
                'bcDiscographyPath': '/band/3/discography',
                'bcAlbumPath': '/album/2/info',
                'bcTrackPath': '/track/3/info'
            }
        }
        cls.LOG = logging.getLogger('BandcampTest')
        with open('test/mock_data/brian_gray_discography.json') as json_file:
            cls.mock_discography_data = json.load(json_file)
        with open('test/mock_data/also_this_other_stuff_album.json') as json_file:
            cls.mock_album_data = json.load(json_file)
        cls.also_this_other_stuff_album_id = 1047117555
        with open('test/mock_data/pi_day_track.json') as json_file:
            cls.mock_track_data = json.load(json_file)
        cls.pi_day_track_id = 2923511621

    def setUp(self):
        self.bandcamp = Bandcamp(self.config, self.LOG)

    @responses.activate
    def test_get_band_from_bc(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcDiscographyPath"]}',
            json=self.mock_discography_data,
            status=HTTPStatus.OK
        )

        band = self.bandcamp.get_band_from_bc(
            self.config['bandcamp']['bcBandIDs'][0])

        self.assertEqual(3, len(band['discography']))
        self.assertEqual(
            self.config['bandcamp']['bcBandIDs'][0], band['discography'][0]['band_id'])

    @responses.activate
    def test_get_band_from_bc_not_found(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcDiscographyPath"]}',
            json='',
            status=HTTPStatus.NOT_FOUND
        )

        try:
            band = self.bandcamp.get_band_from_bc(
                self.config['bandcamp']['bcBandIDs'][0])
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.NOT_FOUND,
                             e.response.status_code)

    @responses.activate
    def test_get_band_from_bc_internal_error(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcDiscographyPath"]}',
            json='',
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

        try:
            band = self.bandcamp.get_band_from_bc(
                self.config['bandcamp']['bcBandIDs'][0])
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.INTERNAL_SERVER_ERROR,
                             e.response.status_code)

    @responses.activate
    def test_get_album_from_bc(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcAlbumPath"]}',
            json=self.mock_album_data,
            status=HTTPStatus.OK
        )

        album = self.bandcamp.get_album_from_bc(
            self.also_this_other_stuff_album_id)

        self.assertEqual(4, len(album['tracks']))
        self.assertEqual(
            self.also_this_other_stuff_album_id, album['tracks'][0]['album_id'])

    @responses.activate
    def test_get_album_from_bc_internal_error(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcAlbumPath"]}',
            json='',
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

        try:
            album = self.bandcamp.get_album_from_bc(
                self.also_this_other_stuff_album_id)
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.INTERNAL_SERVER_ERROR,
                             e.response.status_code)

    @responses.activate
    def test_get_album_from_bc_not_found(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcAlbumPath"]}',
            json='',
            status=HTTPStatus.NOT_FOUND
        )

        try:
            album = self.bandcamp.get_album_from_bc(
                self.also_this_other_stuff_album_id)
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.NOT_FOUND,
                             e.response.status_code)

    @responses.activate
    def test_get_track_from_bc(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcTrackPath"]}',
            json=self.mock_track_data,
            status=HTTPStatus.OK
        )

        track = self.bandcamp.get_track_from_bc(self.pi_day_track_id)

        self.assertEqual('π Day', track['title'])

    @responses.activate
    def test_get_track_from_bc_internal_error(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcTrackPath"]}',
            json='',
            status=HTTPStatus.INTERNAL_SERVER_ERROR
        )

        try:
            track = self.bandcamp.get_track_from_bc(self.pi_day_track_id)
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.INTERNAL_SERVER_ERROR,
                             e.response.status_code)

    @responses.activate
    def test_get_track_from_bc_not_found(self):
        responses.add(
            responses.GET,
            f'{self.config["bandcamp"]["bcApiUrl"]}{self.config["bandcamp"]["bcTrackPath"]}',
            json='',
            status=HTTPStatus.NOT_FOUND
        )

        try:
            track = self.bandcamp.get_track_from_bc(self.pi_day_track_id)
            self.fail()
        except (HTTPError) as e:
            self.assertFalse(e.response.ok)
            self.assertEqual(HTTPStatus.NOT_FOUND,
                             e.response.status_code)


if __name__ == '__main__':
    unittest.main()
