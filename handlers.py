import boto3
import logging
import os
from handler import DatabaseHandler, DiscographyHandler, BadgesHandler, init_config
from database import DatabaseService
from discography import DiscographyService
from badge import BadgeService


LOG = logging.getLogger()
LOG.setLevel(os.getenv('log_level', 'INFO'))
LOG.addHandler(logging.StreamHandler())

config = init_config(LOG)

album_table = boto3.resource('dynamodb').Table(f'{os.getenv("stackName")}-{config["aws"]["albumTable"]}')
track_table = boto3.resource('dynamodb').Table(f'{os.getenv("stackName")}-{config["aws"]["trackTable"]}')

badge_service = BadgeService(config, LOG)
database_service = DatabaseService(config, LOG, album_table, track_table)
discography_service = DiscographyService(config, LOG, album_table, track_table, badge_service.core)

badges_handler = BadgesHandler(config, LOG, badge_service)
database_handler = DatabaseHandler(config, LOG, database_service)
discography_handler = DiscographyHandler(config, LOG, discography_service, badge_service)


def handle_database_refresh(event, context):
    LOG.debug(f'handle_database triggered with event {event}')
    return database_handler.handle(event, context)


def handle_discography(event, context):
    LOG.debug(f'handle_discography triggered with event {event}')
    return discography_handler.handle(event, context)


def handle_badges(event, context):
    LOG.debug(f'handle_badges triggered with event {event}')
    return badges_handler.handle(event, context)
