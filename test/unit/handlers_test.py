import boto3
import builtins
from handler import *
import json
import logging
import os
import unittest
from unittest.mock import *
import yaml


class HandlersUnitTest(unittest.TestCase):
    @classmethod
    @patch.dict(os.environ, {
        'config': 'test/mock_data/mock_config.yml',
        'secretsFile': 'test/mock_data/mock_secrets.yml'
    })
    def setUpClass(cls):
        cls.LOG = logging.getLogger('HandlersUnitTest')
        cls.log_for_systems_under_test = MagicMock()
        cls.config = init_config(cls.LOG)

    @patch('badge.BadgeService')
    @patch('discography.DiscographyService')
    def setUp(self, badge_service, discography_service):
        self.badge_service = badge_service
        self.discography_service = discography_service
        self.badges_handler = BadgesHandler(
            self.config, self.log_for_systems_under_test, badge_service)
        self.discography_handler = DiscographyHandler(
            self.config, self.log_for_systems_under_test, discography_service, badge_service)
        self.refresh_handler = RefreshCacheHandler(
            self.config, self.log_for_systems_under_test, discography_service)

    @patch.dict(os.environ, {
        'config': 'test/mock_data/mock_config.yml',
        'secretsFile': 'test/mock_data/mock_secrets.yml'
    })
    def test_config_local(self):
        final_config = init_config(self.LOG)
        self.assertEqual('laKNKjbnUCw7tnQHnwhSi5gkEmqsZj6B3Qx_Mqm7zro=',
                         final_config['badges']['encryptionKey'])

    @patch.dict(os.environ, {
        'config': 'test/mock_data/mock_config.yml',
        'secretsBucket': 'secrets_bucket',
        'secretsFile': 'test/mock_data/mock_secrets.yml'
    })
    @patch('handler.config.boto3')
    def test_config_s3(self, mock_aws_client):
        with open('test/mock_data/mock_secrets.yml') as secret_config_file:
            s3_obj = {'Body': secret_config_file.read()}
        s3_client = MagicMock()
        s3_client.get_object.return_value = s3_obj
        mock_aws_client.client.return_value = s3_client
        final_config = init_config(self.LOG)
        self.assertEqual('laKNKjbnUCw7tnQHnwhSi5gkEmqsZj6B3Qx_Mqm7zro=',
                         final_config['badges']['encryptionKey'])

    def test_create_new_badge(self):
        self.badge_service.create_token.return_value = '47474747'
        result = self.badges_handler.handle({}, None)
        self.assertEqual(0, len(result['badges']))
        self.assertEqual('47474747', result['token'])

    def test_valid_badge_token(self):
        self.badge_service.get_badges_from_token.return_value = (None, ['k'])
        result = self.badges_handler.handle({'token': '47474747'}, None)
        self.assertIn('k', result['badges'])
        self.assertEqual('47474747', result['token'])

    def test_invalid_badge_token(self):
        self.badge_service.create_token.return_value = '47474747'
        self.badge_service.get_badges_from_token.side_effect = ValueError()
        try:
            result = self.badges_handler.handle({'token': '48484848'}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.warning.assert_called()
            self.assertEqual(HTTPStatus.UNAUTHORIZED, e.args[0]['errorCode'])
            self.assertEqual(0, len(e.args[0]['badges']))
            self.assertEqual('47474747', e.args[0]['token'])

    def test_successful_add_badge_to_token(self):
        self.badge_service.add_badge_to_token.return_value = (
            ['k'], '48484848')
        result = self.badges_handler.handle(
            {'token': '47474747', 'key': 'karaokey'}, None)
        self.assertEqual('48484848', result['token'])
        self.assertIn('k', result['badges'])

    def test_add_badge_to_invalid_token(self):
        self.badge_service.create_token.return_value = '47474747'
        self.badge_service.add_badge_to_token.side_effect = ValueError()
        try:
            result = self.badges_handler.handle(
                {'token': '48484848', 'key': 'karaokey'}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.warning.assert_called()
            self.assertEqual(HTTPStatus.UNAUTHORIZED, e.args[0]['errorCode'])
            self.assertEqual(0, len(e.args[0]['badges']))
            self.assertEqual('47474747', e.args[0]['token'])

    def test_add_invalid_badge_to_valid_token(self):
        self.badge_service.add_badge_to_token.side_effect = KeyError()
        self.badge_service.get_badges_from_token.return_value = (None, ['k'])
        try:
            result = self.badges_handler.handle(
                {'token': '47474747', 'key': 'karaokay'}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.warning.assert_called()
            self.assertEqual(HTTPStatus.BAD_REQUEST, e.args[0]['errorCode'])
            self.assertEqual(1, len(e.args[0]['badges']))
            self.assertIn('k', e.args[0]['badges'])
            self.assertEqual('47474747', e.args[0]['token'])

    def test_get_discography_no_token(self):
        self.badge_service.create_token.return_value = '47474747'
        self.badge_service.get_badges_from_token.return_value = (None, [])
        self.discography_service.get_discography.return_value = [
            {'albumId': 1234567890}
        ]
        result = self.discography_handler.handle({}, None)
        self.assertEqual(0, len(result['badges']))
        self.assertEqual('47474747', result['token'])
        self.assertEqual(1, len(result['discography']))
        self.assertEqual(1234567890, result['discography'][0]['albumId'])

    def test_get_discography_bad_token(self):
        self.badge_service.get_badges_from_token.side_effect = ValueError()
        self.badge_service.create_token.return_value = '47474747'
        self.discography_service.get_discography.return_value = [
            {'albumId': 1234567890}
        ]
        try:
            result = self.discography_handler.handle(
                {'token': '48484848'}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.warning.assert_called()
            self.assertEqual(HTTPStatus.UNAUTHORIZED, e.args[0]['errorCode'])
            self.assertEqual(0, len(e.args[0]['badges']))
            self.assertEqual('47474747', e.args[0]['token'])
            self.assertEqual(1, len(e.args[0]['discography']))
            self.assertEqual(
                1234567890, e.args[0]['discography'][0]['albumId'])

    def test_get_discography_internal_error(self):
        self.badge_service.create_token.return_value = '47474747'
        self.badge_service.get_badges_from_token.return_value = (None, [])
        self.discography_service.get_discography.side_effect = Exception()
        try:
            result = self.discography_handler.handle(
                {'token': 'ƒøøßå®'}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.exception.assert_called()
            self.assertEqual(HTTPStatus.INTERNAL_SERVER_ERROR,
                             e.args[0]['errorCode'])
            self.assertEqual(0, len(e.args[0]['badges']))
            self.assertEqual('ƒøøßå®', e.args[0]['token'])
            self.assertIsNone(e.args[0]['discography'])

    def test_trigger_cache_refresh(self):
        self.refresh_handler.handle({}, None)
        self.discography_service.trigger_cache_refresh.assert_called_with()

    def test_trigger_refresh_internal_error(self):
        self.discography_service.trigger_cache_refresh.side_effect = Exception()
        try:
            self.refresh_handler.handle({}, None)
            self.fail()
        except HandlerBase.LambdaError as e:
            self.log_for_systems_under_test.exception.assert_called()
            self.assertEqual(HTTPStatus.INTERNAL_SERVER_ERROR,
                             e.args[0]['errorCode'])

    def test_refresh_cache(self):
        event = {
            'Records': [
                {
                    'EventSource': 'aws:sns',
                    'Sns': {
                        'TopicArn': 'arn:aws:sns:us-east-1:028568048704:RefreshDiscographyCache'
                    }
                }
            ]
        }
        self.refresh_handler.handle(event, None)
        self.discography_service.refresh_cache.assert_called_with()


if __name__ == '__main__':
    unittest.main()
