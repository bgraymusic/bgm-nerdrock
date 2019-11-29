import json
import logging
import unittest
import handlers

class BadgesTest(unittest.TestCase):
  def setUp(self):
    self.LOG = logging.getLogger('badges_test')
    self.LOG.setLevel('INFO')
    self.good_empty_token = 'gAAAAABd3CqXAwESrtYkIjS-aoKU59DMBPXfGHxAmTYsDekbf9P-DRgrbqASXlG9E3GYflkztalAWl4_zebqQiVkGCVHq6MXdENJ2XzsICdcHZaw6uroMMY='
    self.bad_token = 'kjyutbwvityanlskjhtnalksbtlavkjshtkausblktvuabslktuylbkavsutylbkavsuylktybavslkdtbvlkas'

  def test_create_new_token(self):
    result = handlers.handle_badges(event={}, context={})
    self.LOG.info(json.dumps(result))

  def test_validate_good_token(self):
    result = handlers.handle_badges(event={'token':self.good_empty_token}, context={})
    self.LOG.info(json.dumps(result))

  def test_validate_bad_token(self):
    result = handlers.handle_badges(event={'token': self.bad_token}, context={})
    self.LOG.info(json.dumps(result))

  def test_add_badge_to_token(self):
    result = handlers.handle_badges(event={'token': self.good_empty_token, 'key': 'emptyoke'}, context={})
    self.LOG.info(json.dumps(result))
