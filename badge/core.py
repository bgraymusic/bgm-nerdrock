import enum, json
# from Crypto.Cipher import AES
from cryptography.fernet import Fernet


class Badge(enum.Enum):
		PATREON = enum.auto
		SPINTUNES = enum.auto
		JCC = enum.auto
		KARAOKE = enum.auto
		SFW = enum.auto


class BadgeCore:
	def __init__(self, config, LOG):
		self.config = config
		self.LOG = LOG
# 		self.cipher = AES.new(config['badges']['encryption_key'])
		self.cipher = Fernet(config['badges']['encryption_key'].encode())

	def get_badges_from_token(self, token):
		if self.is_valid_token(token):
			return self.extract_data_from_token(token)['Badges']
		else:
			raise ValueError('Invalid badge token')

	def is_valid_token(self, token):
		token_data = self.extract_data_from_token(token)
		encoded_token_data = token_data['EncryptedBadges'].encode()
		decrypted_token_data = self.cipher.decrypt(encoded_token_data)
		json_token_data = decrypted_token_data.decode()
		enc_badges = json.loads(json_token_data)
		return sorted(token_data['Badges']) == sorted(enc_badges)

	def is_valid_key(self, key):
		for badge in self.config['badges']['badges']:
			self.LOG.info(f'Key found: {badge["key"]}')
		return next((spec for spec in self.config['badges']['badges'] if spec['key'] == key), None) != None

	def get_spec_for_key(self, key):
		return next(spec for spec in self.config['badges']['badges'] if spec['key'] == key)

	def generate_token(self, badges):
		json_str = json.dumps(badges)
		padded_json = self.pad_string_to_multiple_of_16(json_str)
		encrypted_json = self.cipher.encrypt(padded_json.encode()).decode()
		token = '|'.join([json_str, encrypted_json])
		return token

	def extract_data_from_token(self, token):
		return {
			'Badges': json.loads(token.split('|')[0]),
			'EncryptedBadges' : token.split('|')[1]
		}

	def pad_string_to_multiple_of_16(self, s):
		return s if len(s) % 16 == 0 else s + (' ' * (16 - len(s) % 16))
