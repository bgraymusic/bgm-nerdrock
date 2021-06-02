from badge.core import BadgeCore


class BadgeService:

    def __init__(self, config, LOG):
        self.config = config
        self.LOG = LOG
        self.core = BadgeCore(
            config['badges']['badges'], config['badges']['encryptionKey'], LOG)

    def create_token(self):
        return self.core.badge_codes_to_token([])

    def get_badges_from_token(self, token):
        if not self.core.is_valid_token(token):
            raise ValueError(f'Token value {token} is invalid')
        else:
            badges = []
            badge_codes = self.core.token_to_badge_codes(token)
            for code in badge_codes:
                badges.append(self.core.badges_spec[code])
            return badges, badge_codes

    def add_badge_to_token(self, token, key):
        if not self.core.is_valid_token(token):
            raise ValueError(f'Token value {token} is invalid')
        elif not self.core.is_valid_key(key):
            raise KeyError(f'Key value {key} is invalid')
        else:
            badge_codes = self.core.token_to_badge_codes(token)
            spec = self.core.get_spec_for_key(key)
            addedCode = None
            if not spec['code'] in badge_codes:
                badge_codes.append(spec['code'])
                addedCode = spec['code']
            return badge_codes, self.core.badge_codes_to_token(badge_codes), addedCode
