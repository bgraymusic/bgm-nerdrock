import boto3
import deepmerge
from http import HTTPStatus
import json
import logging
import os
import requests
import yaml
from discography.service import DiscographyService
from badge.service import BadgeService


LOG = logging.getLogger()
LOG.setLevel(os.getenv('log_level', 'DEBUG'))
LOG.addHandler(logging.StreamHandler())


def init_config():
    public_config = yaml.load(
        open(os.getenv('config', 'config.yml')).read(), Loader=yaml.BaseLoader)
    secret_config_bucket = os.getenv('secretsBucket', None)
    secret_config_file = os.getenv('secretsFile', 'secrets.yml')
    if secret_config_bucket != None:
        s3_client = boto3.client('s3')
        s3_obj = s3_client.get_object(
            Bucket=secret_config_bucket, Key=secret_config_file)
        secret_config = yaml.load(s3_obj['Body'], Loader=yaml.BaseLoader)
    else:
        secret_config = yaml.load(
            open(secret_config_file).read(), Loader=yaml.BaseLoader)
    final_config = deepmerge.always_merger.merge(public_config, secret_config)
    LOG.debug(f'final config: {json.dumps(final_config)}')
    return final_config


config = init_config()
discography_service = DiscographyService(config, LOG)
badge_service = BadgeService(config, LOG)


class BadgeLambdaResult(dict):
    def __init__(self, message, badges, token):
        self['message'] = message
        self['badges'] = badges
        self['token'] = token

class LambdaError(Exception):
    def __init__(self, status, result):
        result['message'] = f'[{status}] {result["message"]}'
        super().__init__(result)
        self.errorCode = status


def handle_discography(event, context):
    LOG.debug(f'handle_discography triggered with event {event}')
    resultStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    resultBody = {}
    try:
        if is_refresh_trigger_event(event):
            discography_service.refresh_cache()
            resultStatus = HTTPStatus.OK
        else:
            no_cache = 'no_cache' in event and event['no_cache']
            badges = []
            if 'token' in event:
                badges = badge_service.get_badges_from_token(
                    token=event['token'])
            response = discography_service.get_discography(
                badges=badges, no_cache=no_cache)
            resultStatus = HTTPStatus.OK
            resultBody = response
    except Exception as e:
        resultStatus = HTTPStatus.INTERNAL_SERVER_ERROR
        resultBody = {'err': f'{e}'}
    return create_http_result(resultStatus, resultBody)


def handle_refresh_discography_cache(event, context):
    resultStatus = HTTPStatus.INTERNAL_SERVER_ERROR
    resultBody = {}
    try:
        discography_service.trigger_cache_refresh()
        resultStatus = HTTPStatus.OK
        resultBody = {'msg': 'Cache refresh triggered'}
    except Exception as e:
        resultStatus = HTTPStatus.INTERNAL_SERVER_ERROR
        resultBody = {'err': f'{e}'}
    return create_http_result(resultStatus, resultBody)


def handle_badges(event, context):
    LOG.debug(f'handle_badges triggered with event {event}')
    if not 'token' in event:
        return BadgeLambdaResult('New, empty token created', [], badge_service.create_token())
    elif not 'key' in event:
        try:
            __, badgeCodes = badge_service.get_badges_from_token(
                event['token'])
            return BadgeLambdaResult(f'[200] Token {event["token"]} is valid', badgeCodes, event['token'])
        except ValueError as e:
            raise LambdaError(HTTPStatus.UNAUTHORIZED, BadgeLambdaResult(
                'Invalid input token', [], badge_service.create_token()))
    else:
        try:
            badges, token = badge_service.add_badge_to_token(event['token'], event['key'])
            return BadgeLambdaResult('Badge added to token', badges, token)
        except ValueError as e:
            raise LambdaError(HTTPStatus.UNAUTHORIZED, BadgeLambdaResult(
                'Invalid input token', [], badge_service.create_token()))
        except KeyError as e:
            __, badgeCodes = badge_service.get_badges_from_token(event['token'])
            raise LambdaError(HTTPStatus.BAD_REQUEST, BadgeLambdaResult(
                'Invalid badge key', badgeCodes, event['token']))


def is_refresh_trigger_event(event):
    return 'Records' in event and len(event['Records']) > 0 and 'EventSource' in event['Records'][0] and event['Records'][0]['EventSource'] == 'aws:sns' and event['Record'][0]['Sns']['TopicArn'].contains(os.getenv['refreshCacheTopic'])


if __name__ == "__main__":
    # execute only if run as a script
    print(json.dumps(handle_discography(
        {'no_cache': True}, None), sort_keys=True, indent=4, separators=(',', ': ')))
