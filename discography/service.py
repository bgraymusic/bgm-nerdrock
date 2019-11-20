from discography.bandcamp import Bandcamp
from badge.core import BadgeCore
import boto3
import os


class DiscographyService:

	def __init__(self, config, LOG):
		self.config = config
		self.bc_key_param = {'key': config['bandcamp']['bcKey']}
		self.LOG = LOG
		self.band_cache = {}
		self.album_cache = {}
		self.bandcamp = Bandcamp(config, LOG)
		self.badge_core = BadgeCore(config, LOG)

	def get_all_albums_from_all_bands(self, no_cache):
		band_ids = self.config['bandcamp']['bcBIDs']
		albums = []
		for band_id in band_ids:
			band = self.get_band(band_id, no_cache)
			for album_id in band['discography']:
					albums.append(self.get_album(album_id))
		return albums

	def get_band(self, band_id, no_cache):
		if not no_cache and band_id in self.band_cache:
			return self.band_cache[band_id]
		else:
			band = self.bandcamp.get_band_from_bc(band_id)
			self.band_cache[band_id] = band
			return band

	def get_selected_albums(self, album_list, no_cache):
		albums = []
		for album in album_list:
				albums.append(self.get_album(album))
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
		sns_client.publish(
			TopicArn=os.getenv['refreshCacheTopic'], Message='{}')
		self.LOG.info(f'Cache refresh triggered')

	def refresh_cache(self):
		self.album_cache = {}
		self.get_all_albums_from_all_bands(True)
		self.LOG.info(f'Cache refreshed')
