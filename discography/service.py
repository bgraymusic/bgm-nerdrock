from discography.bandcamp import Bandcamp
from badge.core import BadgeCore
import boto3
import os


class DiscographyService:

    def __init__(self, config, LOG):
        self.config = config
        self.LOG = LOG
        self.band_cache = {}
        self.album_cache = {}
        self.bandcamp = Bandcamp(config, LOG)
        self.badge_core = BadgeCore(
            config['badges']['badges'], config['badges']['encryptionKey'], LOG)

    def get_discography(self, badges, no_cache):
        album_ids = self.get_album_ids_for_badges(badges)
        self.LOG.debug(f'Fetching discography for albums: {album_ids}')
        return self.get_selected_albums(album_ids, no_cache)

    def get_all_albums_from_all_bands(self, no_cache):
        band_ids = self.config['bandcamp']['bcBandIDs']
        albums = []
        for band_id in band_ids:
            band = self.get_band(band_id, no_cache)
            for album in band['discography']:
                albums.append(self.get_album(album['album_id'], no_cache))
        return albums

    def get_band(self, band_id, no_cache):
        if not no_cache and band_id in self.band_cache:
            return self.band_cache[band_id]
        else:
            band = self.bandcamp.get_band_from_bc(band_id)
            self.band_cache[band_id] = band
            return band

    def get_selected_albums(self, album_ids, no_cache):
        albums = []
        for album_id in album_ids:
            albums.append(self.get_album(album_id, no_cache))
        return albums

    def get_album(self, album_id, no_cache):
        if not no_cache and album_id in self.album_cache:
            return self.album_cache[album_id]
        else:
            album = self.bandcamp.get_album_from_bc(album_id)
            self.album_cache[album_id] = album
            return album

    def trigger_cache_refresh(self):
        sns_client = boto3.client('sns')
        self.LOG.debug(
            f'Publishing on SNS topic {self.config["aws"]["sns"]["refreshDiscographyCache"]["arn"]}')

        sns_client.publish(
            TopicArn=self.config['aws']['sns']['refreshDiscographyCache']['arn'], Message='{}')
        self.LOG.info(f'Cache refresh triggered')

    def refresh_cache(self):
        self.album_cache = {}
        self.get_all_albums_from_all_bands(True)
        self.LOG.info(f'Cache refreshed')

    def get_album_ids_for_badges(self, badges):
        self.LOG.debug(f'get_album_ids_for_badges was sent badges: {badges}')
        album_ids = self.config['badges']['defaultAlbumIDs']
        for badge_key in badges:
            spec = self.badge_core.badges_spec[badge_key]
            self.LOG.debug(f'spec for badge {badge_key}: {spec}')
            if spec and 'albumIDs' in spec:
                album_ids += spec['albumIDs']
        return album_ids
