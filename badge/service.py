from badge.core import BadgeCore

class BadgeService:

	def __init__(self, config, LOG):
		self.config = config
		self.LOG = LOG
		self.core = BadgeCore(config, LOG)

	def create_badge_token(self):
		return self.core.generate_token([])


	def add_badge_to_token(self, token, key):
		if not self.core.is_valid_token(token):
			self.LOG.info(f'Invalid token: {token}')
			return self.core.generate_token([])
		elif not self.core.is_valid_key(key):
			self.LOG.info(f'Invalid key: {key}')
			return token
		else:
			token_data = self.core.extract_data_from_token(token)
			spec = self.core.get_spec_for_key(key)
			if (spec['code'] in token_data['Badges']):
				return token
			token_data['Badges'].append(spec['code'])
			return self.core.generate_token(token_data['Badges'])
