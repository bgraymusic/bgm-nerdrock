import logging
import unittest
from unittest.mock import *
import handlers
from handler import *


class DiscographyTest(unittest.TestCase):
    def setUp(self):
        self.LOG = logging.getLogger('discography_test')
        self.LOG.setLevel('INFO')
        self.good_empty_token = 'gAAAAABd3CqXAwESrtYkIjS-aoKU59DMBPXfGHxAmTYsDekbf9P-DRgrbqASXlG9E3GYflkztalAWl4_zebqQiVkGCVHq6MXdENJ2XzsICdcHZaw6uroMMY='
        self.good_token_with_karaoke = 'gAAAAABd5a9WeZafUy2IwnNGnwbl2Lfp54Hn5mjUal9Hb6XnboLmFqMQGufS5QxDxcai_tZ_pJOREyqRzYgwgidmgAk4pYOxDgkY6j9ZeTDj-7klq6_jB44='
        self.bad_token = 'kjyutbwvityanlskjhtnalksbtlavkjshtkausblktvuabslktuylbkavsutylbkavsuylktybavslkdtbvlkas'
        handlers.LOG = MagicMock()

    def test_get_with_no_token(self):
        no_token_result = handlers.handle_discography(event={}, context={})
        self.assertIn('discography', no_token_result)
        self.assertEqual(3, len(no_token_result['discography']))
        self.assertEqual(no_token_result['badges'], [])
        self.assertIn('token', no_token_result)
        self.assertIsNotNone(no_token_result['token'])
        verify = handlers.handle_badges(
            event={'token': no_token_result['token']}, context={})

    def test_get_with_good_empty_token(self):
        empty_token_result = handlers.handle_discography(
            event={'token': self.good_empty_token}, context={})
        self.assertIn('discography', empty_token_result)
        self.assertEqual(3, len(empty_token_result['discography']))
        self.assertEqual(empty_token_result['badges'], [])
        self.assertIn('token', empty_token_result)
        self.assertIsNotNone(empty_token_result['token'])
        verify = handlers.handle_badges(
            event={'token': empty_token_result['token']}, context={})

    def test_get_with_bad_token(self):
        with self.assertRaises(HandlerBase.InvalidTokenError):
            handlers.handle_discography(
                event={'token': self.bad_token}, context={})

    def test_get_with_karaoke(self):
        karaoke_token_result = handlers.handle_discography(
            event={'token': self.good_token_with_karaoke}, context={})
        self.assertIn('discography', karaoke_token_result)
        self.assertEqual(4, len(karaoke_token_result['discography']))
        self.assertEqual(karaoke_token_result['badges'], ['k'])
        self.assertIn('token', karaoke_token_result)
        self.assertIsNotNone(karaoke_token_result['token'])
        verify = handlers.handle_badges(
            event={'token': karaoke_token_result['token']}, context={})


if __name__ == '__main__':
    unittest.main()
