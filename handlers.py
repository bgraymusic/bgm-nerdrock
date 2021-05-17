import json
import logging
import os
from handler import DiscographyHandler, BadgesHandler, RefreshCacheHandler, init_config
from discography import DiscographyService
from badge import BadgeService


LOG = logging.getLogger()
LOG.setLevel(os.getenv('log_level', 'INFO'))
LOG.addHandler(logging.StreamHandler())

config = init_config(LOG)

discography_service = DiscographyService(config, LOG)
badge_service = BadgeService(config, LOG)
discography_handler = DiscographyHandler(
    config, LOG, discography_service, badge_service)
refresh_handler = RefreshCacheHandler(config, LOG, discography_service)
badges_handler = BadgesHandler(config, LOG, badge_service)


def handle_test(event, context):
    LOG.debug(f'handle_test triggered with event {event}')
    return test_handler.handle(event, context)

def handle_discography(event, context):
    LOG.debug(f'handle_discography triggered with event {event}')
    return discography_handler.handle(event, context)


def handle_refresh_discography_cache(event, context):
    LOG.debug(f'handle_refresh_discography_cachs triggered with event {event}')
    return refresh_handler.handle(event, context)


def handle_badges(event, context):
    LOG.debug(f'handle_badges triggered with event {event}')
    return badges_handler.handle(event, context)
