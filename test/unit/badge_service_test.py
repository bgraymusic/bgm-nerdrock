import logging
import unittest
from badge import BadgeService

# This badge stuff doesn't have any external dependencies that run remotely or
# would in any way take the kind of time that exceeds spec for a "unit" test.
# Therefore we have no mocks, and only one test case that exercises both the
# service and core layers at the same time.


class BadgeServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = {
            'badges': {
                'encryptionKey': 'laKNKjbnUCw7tnQHnwhSi5gkEmqsZj6B3Qx_Mqm7zro=',
                'defaultAlbumIDs': [1047117555],
                'badges': {
                    'k': {
                        'code': 'k',
                        'enum': 'Karaoke',
                        'key': 'karaoke',
                        'albumIDs': [1234567890]
                    }
                }
            }
        }
        cls.LOG = logging.getLogger('BadgeServiceTest')

    def setUp(self):
        self.badge_service = BadgeService(self.config, self.LOG)

    def test_token_happy_path(self):
        token = self.badge_service.create_token()
        badges, badge_codes = self.badge_service.get_badges_from_token(token)
        self.assertEqual(0, len(badges))
        self.assertEqual(0, len(badge_codes))
        new_badges, new_token = self.badge_service.add_badge_to_token(
            token, self.config['badges']['badges']['k']['key'])
        self.assertIn('k', new_badges)
        check_new_badges, check_new_badge_codes = self.badge_service.get_badges_from_token(
            new_token)
        self.assertEqual('k', check_new_badges[0]['code'])
        self.assertIn('k', check_new_badge_codes)
        new_badges, new_token = self.badge_service.add_badge_to_token(
            new_token, self.config['badges']['badges']['k']['key'])
        self.assertIn('k', new_badges)
        check_new_badges, check_new_badge_codes = self.badge_service.get_badges_from_token(
            new_token)
        self.assertEqual('k', check_new_badges[0]['code'])
        self.assertIn('k', check_new_badge_codes)

    def test_bad_token(self):
        token = 'BAD_TOKEN'
        try:
            self.badge_service.get_badges_from_token(token)
            self.fail()
        except ValueError:
            pass

    def test_bad_code_in_token(self):
        token = self.badge_service.core.badge_codes_to_token(['BAD_CODE'])
        try:
            self.badge_service.get_badges_from_token(token)
            self.fail()
        except ValueError:
            pass
        try:
            self.badge_service.add_badge_to_token(
                token, self.config['badges']['badges']['k']['key'])
            self.fail()
        except ValueError:
            pass

    def test_bad_key_added(self):
        token = self.badge_service.create_token()
        badges, badge_codes = self.badge_service.get_badges_from_token(token)
        self.assertEqual(0, len(badges))
        self.assertEqual(0, len(badge_codes))
        try:
            _, _ = self.badge_service.add_badge_to_token(
                token, 'BAD_KEY')
            self.fail()
        except KeyError:
            pass
