import boto3
import json
import logging
import unittest
from unittest.mock import *
from discography import *


class DiscographyServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open('test/mock_data/brian_gray_discography.json') as json_file:
            cls.mock_discography_data = json.load(json_file)
        with open('test/mock_data/also_this_other_stuff_album.json') as json_file:
            cls.mock_album_data = json.load(json_file)
        cls.also_this_other_stuff_album_id = 1047117555
        with open('test/mock_data/pi_day_track.json') as json_file:
            cls.mock_track_data = json.load(json_file)
        cls.config = {
            'aws': {
                'sns': {
                    'refreshDiscographyCache': {
                        'arn': 'arn:aws:sns:us-east-1:123456789012:RefreshDiscographyCache'
                    }
                }
            },
            'bandcamp': {
                'bcBandIDs': [230945364]
            },
            'badges': {
                'defaultAlbumIDs': [cls.also_this_other_stuff_album_id],
                'badges': {
                    'k': {
                        'code': 'k',
                        'enum': 'Karaoke',
                        'key': 'karaoke',
                        'albumIDs': [1234567890]
                    },
                    's': {
                        'code': 's',
                        'enum': 'SafeForWork',
                        'key': 'sfw'
                    }
                }
            }
        }
        cls.LOG = logging.getLogger('DiscographyServiceTest')

    @patch('discography.Bandcamp')
    @patch('badge.BadgeCore')
    def setUp(self, bandcamp, badge_core):
        self.bandcamp = bandcamp
        self.badge_core = badge_core
        self.badge_core.badges_spec = self.config['badges']['badges']
        self.discography_service = DiscographyService(
            self.config, self.LOG, bandcamp=bandcamp, badge_core=badge_core)

    def test_get_discography_no_badges(self):
        self.bandcamp.get_album_from_bc.return_value = self.mock_album_data
        self.bandcamp.get_track_from_bc.return_value = self.mock_track_data
        compare_tracks = list(
            map(lambda x: x['track_id'], self.mock_album_data['tracks']))

        result = self.discography_service.get_discography([], False)

        self.bandcamp.get_album_from_bc.assert_called_with(
            self.also_this_other_stuff_album_id)
        for track_id in compare_tracks:
            self.bandcamp.get_track_from_bc.assert_any_call(track_id)
        self.assertEqual(1, len(result))
        self.assertEqual(4, len(result[0]['tracks']))

    def test_get_discography_from_cache(self):
        self.bandcamp.get_album_from_bc.return_value = {}
        self.discography_service.album_cache[self.mock_album_data['album_id']
                                             ] = self.mock_album_data
        compare_tracks = list(
            map(lambda x: x['track_id'], self.mock_album_data['tracks']))

        result = self.discography_service.get_discography([], False)

        self.assertEqual(1, len(result))
        self.assertEqual(4, len(result[0]['tracks']))

    def test_get_discography_with_badges(self):
        self.bandcamp.get_album_from_bc.return_value = self.mock_album_data
        self.bandcamp.get_track_from_bc.return_value = self.mock_track_data
        compare_tracks = list(
            map(lambda x: x['track_id'], self.mock_album_data['tracks']))

        result = self.discography_service.get_discography(
            [self.config['badges']['badges']['k']['code'], self.config['badges']['badges']['s']['code']], False)

        self.bandcamp.get_album_from_bc.assert_any_call(
            self.also_this_other_stuff_album_id)
        self.bandcamp.get_album_from_bc.assert_any_call(
            self.config['badges']['badges']['k']['albumIDs'][0])
        for track_id in compare_tracks:
            self.bandcamp.get_track_from_bc.assert_any_call(track_id)
        self.assertEqual(2, len(result))
        self.assertEqual(4, len(result[0]['tracks']))
        self.assertEqual(4, len(result[1]['tracks']))

    def test_get_band(self):
        self.bandcamp.get_band_from_bc.return_value = self.mock_discography_data
        compare_albums = list(
            map(lambda x: x['album_id'], self.mock_discography_data['discography']))

        result = self.discography_service.get_band(
            self.config['bandcamp']['bcBandIDs'][0], False)

        self.bandcamp.get_band_from_bc.assert_called_with(
            self.config['bandcamp']['bcBandIDs'][0])
        for album in result['discography']:
            self.assertIn(album['album_id'], compare_albums)

    def test_get_band_from_cache(self):
        self.bandcamp.get_band_from_bc.return_value = {}
        self.discography_service.band_cache[self.config['bandcamp']
                                            ['bcBandIDs'][0]] = self.mock_discography_data
        compare_albums = list(
            map(lambda x: x['album_id'], self.mock_discography_data['discography']))

        result = self.discography_service.get_band(
            self.config['bandcamp']['bcBandIDs'][0], False)

        for album in result['discography']:
            self.assertIn(album['album_id'], compare_albums)

    @patch('boto3.client')
    def test_trigger_cache_refresh(self, mock_boto3_client_factory):
        mock_boto3_sns_client = MagicMock()
        mock_boto3_client_factory.return_value = mock_boto3_sns_client

        self.discography_service.trigger_cache_refresh()

        mock_boto3_client_factory.assert_called_with('sns')
        mock_boto3_sns_client.publish.assert_called_with(
            TopicArn=self.config['aws']['sns']['refreshDiscographyCache']['arn'], Message='{}')

    def test_refresh_cache(self):
        self.bandcamp.get_band_from_bc.return_value = self.mock_discography_data
        self.bandcamp.get_album_from_bc.return_value = self.mock_album_data
        self.bandcamp.get_track_from_bc.return_value = self.mock_track_data

        self.discography_service.refresh_cache()


if __name__ == '__main__':
    unittest.main()
