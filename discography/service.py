import configparser
import json
import logging
import requests


class DiscographyService:

	def __init__(self, config, LOG):
		self.config = config
		self.bc_key_param = {'key': config['bandcamp']['bcKey']}
		self.LOG = LOG
		self.cache = {}

	def get_discography(self, no_cache):
	    band_ids = self.config['bandcamp']['bcBIDs']
	    discography = []
	    for band_id in band_ids:
	        if not no_cache and band_id in self.cache:
	            band = self.cache[band_id]
	            self.LOG.info(f'Discography from cache: {band["discography"][0]["artist"]}')
	        else:
	            band = self.get_band(band_id)
	            self.cache[band_id] = band
	        discography = discography + band['discography']
	    return discography

	def get_band(self, band_id):
	    payload = {**self.bc_key_param, **{'band_id': band_id}}
	    band = requests.get(self.config['bandcamp']['bcApiUrl'] + self.config['bandcamp']['bcDiscographyPath'], payload).json()
	    self.LOG.debug(f'Discography from Bandcamp: {band["discography"][0]["artist"]}')
	    for album in band['discography']:
	        album_data = self.get_album(album['album_id'])
	        album.update(album_data)
	    return band

	def get_album(self, album_id):
	    payload = {**self.bc_key_param, **{'album_id': album_id}}
	    album = requests.get(self.config['bandcamp']['bcApiUrl'] + self.config['bandcamp']['bcAlbumPath'], payload).json()
	    self.LOG.debug(f'Album from Bandcamp: {album["title"]}')
	    for track in album['tracks']:
	        track_data = self.get_track(track['track_id'])
	        track.update(track_data)
	    return album

	def get_track(self, track_id):
	    payload = {**self.bc_key_param, **{'track_id': track_id}}
	    track = requests.get(self.config['bandcamp']['bcApiUrl'] + self.config['bandcamp']['bcTrackPath'], payload).json()
	    self.LOG.debug(f'Track from Bandcamp: {track["title"]}')
	    return track
