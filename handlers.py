import json, logging, os
import requests
import yaml
from discography.service import DiscographyService
from badge.service import BadgeService


LOG = logging.getLogger()
LOG.setLevel(os.getenv('log_level', 'DEBUG'))
LOG.addHandler(logging.StreamHandler())

config = yaml.load(open(os.getenv('config', 'config.yml')).read())
discography_service = DiscographyService(config, LOG)
badge_service = BadgeService(config, LOG)


def handle_discography(event, context):
    LOG.debug(f'handle_discography triggered with event {event}')
    no_cache = 'no_cache' in event and event['no_cache']
    response = discography_service.get_discography(no_cache)
    LOG.debug(f'Bandcamp response: {len(response)} albums:')
    for album in response:
        LOG.debug(f'  - {album["title"]}')
    return response


def handle_badges(event, context):
    LOG.debug(f'handle_badges triggered with event {event}')
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'headers': {},
        'body': json.dumps(event)
    }


if __name__ == "__main__":
    # execute only if run as a script
    print(json.dumps(handle_discography({'no_cache': True}, None), sort_keys=True, indent=4, separators=(',', ': ')))
