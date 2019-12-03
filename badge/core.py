import json
from cryptography.fernet import Fernet


class BadgeCore:
    def __init__(self, badges_spec, encryption_key, LOG):
        self.LOG = LOG
        self.badges_spec = badges_spec
        self.cipher = Fernet(encryption_key.encode())

    def is_valid_token(self, token):
        try:
            badge_codes = self.token_to_badge_codes(token)
            for code in badge_codes:
                if code not in self.badges_spec:
                    return False
            return True
        except Exception as e:
            self.LOG.debug(f'is_valid_token threw {type(e)}')
            return False

    def is_valid_key(self, key):
        return self.get_spec_for_key(key) is not None

    def get_spec_for_key(self, key):
        spec = next(
            (self.badges_spec[spec] for spec in self.badges_spec if self.badges_spec[spec]['key'] == key), None)
        return spec

    def badge_codes_to_token(self, badge_codes):
        json_str = json.dumps(badge_codes)
        padded_json = self.pad_string_to_multiple_of_16(json_str)
        encoded_padded_json = padded_json.encode()
        encrypted_token = self.cipher.encrypt(encoded_padded_json)
        return encrypted_token.decode()

    def token_to_badge_codes(self, token):
        encoded_token_data = token.encode()
        decrypted_token_data = self.cipher.decrypt(encoded_token_data)
        decoded_json_token_str = decrypted_token_data.decode()
        return json.loads(decoded_json_token_str)

    def pad_string_to_multiple_of_16(self, s):
        return s if len(s) % 16 == 0 else s + (' ' * (16 - len(s) % 16))
