"""Internal logic to handle badge decryption and validation"""

import json

from cryptography import fernet

from api.runtime import log
from api.runtime import config


class BadgeCore:
    """Internal logic to handle badge decryption and validation"""

    def __init__(self, *, encryption_key: str | None = None, cipher: fernet.Fernet | None = None):
        if encryption_key and cipher:
            raise TypeError(
                'BadgeCore() parameter keys "encryption_key" and "cipher" are mutually exclusive. \
                Provide one of them or neither.')
        self.badges_spec = config.Config.get().badges.badges
        self.encryption_key = encryption_key if encryption_key else config.Config.get().badges.encryption_key
        self.cipher = cipher if cipher else fernet.Fernet(self.encryption_key.encode())

    def is_valid_token(self, token):
        try:
            badge_codes = self.token_to_badge_codes(token)
            for code in badge_codes:
                if code not in self.badges_spec:
                    return False
            return True
        except TypeError as e:
            log.Log.get().debug(f'is_valid_token threw {type(e)}')
            return False
        except fernet.InvalidToken as e:
            log.Log.get().debug(f'is_valid_token threw {type(e)}')
            return False

    def is_valid_key(self, key):
        return self.get_spec_for_key(key) is not None

    def get_spec_for_key(self, key) -> config.Badge | None:
        spec = next(
            (self.badges_spec[spec] for spec in self.badges_spec if self.badges_spec[spec].key == key), None)
        return spec

    def badge_codes_to_token(self, badge_codes: list) -> str:
        json_str = json.dumps(badge_codes)
        padded_json = self.pad_string_to_multiple_of_16(json_str)
        encoded_padded_json = padded_json.encode()
        encrypted_token = self.cipher.encrypt(encoded_padded_json)
        return encrypted_token.decode()

    def token_to_badge_codes(self, token: str) -> list:
        encoded_token_data = token.encode()
        decrypted_token_data = self.cipher.decrypt(encoded_token_data)
        decoded_json_token_str = decrypted_token_data.decode()
        return json.loads(decoded_json_token_str)

    def pad_string_to_multiple_of_16(self, s: str) -> str:
        return s if len(s) % 16 == 0 else s + (' ' * (16 - len(s) % 16))
