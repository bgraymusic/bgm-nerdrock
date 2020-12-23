import boto3
import logging
import unittest
from unittest.mock import *
import handlers
from handler import *


class DiscographyRefreshTest(unittest.TestCase):
    def setUp(self):
        self.LOG = logging.getLogger('discography_test')
        self.LOG.setLevel('INFO')
        handlers.LOG = MagicMock()

    def test_refresh_cache(self):
        pass