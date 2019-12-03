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
LOG.setLevel(os.getenv('log_level', 'INFO'))
LOG.addHandler(logging.StreamHandler())


def init_config():
    public_config = yaml.load(
        open(os.getenv('config', 'config.yml')).read(), Loader=yaml.BaseLoader)
    secret_config_bucket = os.getenv('secretsBucket', None)
    secret_config_file = os.getenv('secretsFile', 'secrets.yml')
    if secret_config_bucket is not None:
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


class DiscographyLambdaResult(dict):
    def __init__(self, message, badges, token, discography):
        self['message'] = message
        self['badges'] = badges
        self['token'] = token
        self['discography'] = discography


class RefreshDiscographyLambdaResult(dict):
    def __init__(self, message):
        self['message'] = message


class LambdaError(Exception):
    def __init__(self, status, result, exc=None):
        result['errorCode'] = status
        result['message'] = f'[{status}] {result["message"]}'
        result['exception'] = exc
        super().__init__(result)


def handle_discography(event, context):
    LOG.debug(f'handle_discography triggered with event {event}')
    try:
        token = event['token'] if 'token' in event else badge_service.create_token()
        __, badge_codes = badge_service.get_badges_from_token(token)
        response = discography_service.get_discography(
            badge_codes, no_cache=False)
        return DiscographyLambdaResult('Discography successfully fetched', badge_codes, token, response)
    except ValueError as e:
        LOG.warning(e.with_traceback)
        token = badge_service.create_token()
        discography = discography_service.get_discography([], no_cache=False)
        raise LambdaError(HTTPStatus.UNAUTHORIZED, DiscographyLambdaResult(
            'Invalid token, creating default', [], token, discography))
    except Exception as e:
        LOG.exception("handlers.handle_discography")
        raise LambdaError(HTTPStatus.INTERNAL_SERVER_ERROR, DiscographyLambdaResult(
            'Internal Server Error', [], event['token'] if 'token' in event else None, None), e)


def handle_refresh_discography_cache(event, context):
    LOG.debug(f'handle_refresh_discography_cachs triggered with event {event}')
    try:
        if is_refresh_trigger_event(event):
            discography_service.refresh_cache()
            return RefreshDiscographyLambdaResult('Discography cache refreshed')
        else:
            discography_service.trigger_cache_refresh()
            return RefreshDiscographyLambdaResult('Discography cache refresh triggered')
    except Exception as e:
        LOG.exception("handlers.handle_refresh_discography_cache")
        raise LambdaError(HTTPStatus.INTERNAL_SERVER_ERROR, DiscographyLambdaResult(
            'Internal Server Error', None, None, None), e)


def handle_badges(event, context):
    LOG.debug(f'handle_badges triggered with event {event}')
    if 'token' not in event:
        return BadgeLambdaResult('New, empty token created', [], badge_service.create_token())
    elif 'key' not in event:
        try:
            __, badgeCodes = badge_service.get_badges_from_token(
                event['token'])
            return BadgeLambdaResult(f'Token {event["token"]} is valid', badgeCodes, event['token'])
        except ValueError as e:
            raise LambdaError(HTTPStatus.UNAUTHORIZED, BadgeLambdaResult(
                'Invalid input token', [], badge_service.create_token()))
    else:
        try:
            badges, token = badge_service.add_badge_to_token(
                event['token'], event['key'])
            return BadgeLambdaResult('Badge added to token', badges, token)
        except ValueError as e:
            raise LambdaError(HTTPStatus.UNAUTHORIZED, BadgeLambdaResult(
                'Invalid input token', [], badge_service.create_token()))
        except KeyError as e:
            __, badgeCodes = badge_service.get_badges_from_token(
                event['token'])
            raise LambdaError(HTTPStatus.BAD_REQUEST, BadgeLambdaResult(
                'Invalid badge key', badgeCodes, event['token']))


def is_refresh_trigger_event(event):
    return ('Records' in event and
            len(event['Records']) > 0 and
            'EventSource' in event['Records'][0] and
            event['Records'][0]['EventSource'] == 'aws:sns' and
            config['aws']['sns']['refreshDiscographyCache']['topic'] in event['Records'][0]['Sns']['TopicArn'])


if __name__ == "__main__":
    # execute only if run as a script
    print(json.dumps(handle_discography(
        {'no_cache': True}, None), sort_keys=True, indent=4, separators=(',', ': ')))
