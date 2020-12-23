import json
import logging
import unittest
from unittest.mock import *
import handlers
from handler.base import HandlerBase


class BadgesTest(unittest.TestCase):
    def setUp(self):
        self.LOG = logging.getLogger('badges_test')
        self.LOG.setLevel('INFO')
        self.good_empty_token = 'gAAAAABd3CqXAwESrtYkIjS-aoKU59DMBPXfGHxAmTYsDekbf9P-DRgrbqASXlG9E3GYflkztalAWl4_zebqQiVkGCVHq6MXdENJ2XzsICdcHZaw6uroMMY='
        self.bad_token = 'kjyutbwvityanlskjhtnalksbtlavkjshtkausblktvuabslktuylbkavsutylbkavsuylktybavslkdtbvlkas'
        handlers.LOG = MagicMock()

    def test_create_new_token(self):
        result = handlers.handle_badges(event={}, context={})
        self.assertEqual(result['badges'], [])
        self.assertIn('token', result)
        self.assertIsNotNone(result['token'])
        verify = handlers.handle_badges(
            event={'token': result['token']}, context={})

    def test_validate_good_token(self):
        result = handlers.handle_badges(
            event={'token': self.good_empty_token}, context={})

    def test_validate_bad_token(self):
        with self.assertRaises(HandlerBase.LambdaError):
            handlers.handle_badges(event={'token': self.bad_token}, context={})

    def test_add_badge_to_token(self):
        result = handlers.handle_badges(
            event={'token': self.good_empty_token, 'key': 'emptyoke'}, context={})
        self.assertEqual(result['badges'], ['k'])


if __name__ == '__main__':
    unittest.main()
