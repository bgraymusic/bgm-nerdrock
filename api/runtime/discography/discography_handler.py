from ..handler_base import (
    HandlerBase, HandlerDescription,
    InvalidTokenError, InternalError,
    ResourceDescription, MethodDescription, HTTPMethod
)
from ..log import Log
from .service import DiscographyService
from ..badges.service import BadgeService


class DiscographyHandler(HandlerBase):
    def __init__(self, *, discography_service: DiscographyService = None, badge_service: BadgeService = None):
        self.discography_service = discography_service if discography_service else DiscographyService()
        self.badge_service = badge_service if badge_service else BadgeService()

    class Result(dict):
        def __init__(self, message, badges, token, discography):
            self['message'] = message
            self['badges'] = badges
            self['token'] = token
            self['discography'] = discography

    def handle(self, event, context):
        if 'keep_warm' in event:
            return DiscographyHandler.Result('Discography handler triggered with keep_warm', None, None, None)

        try:
            token = event['token'] if 'token' in event else self.badge_service.create_token()
            __, badge_codes = self.badge_service.get_badges_from_token(token)
            response = self.discography_service.get_discography(badge_codes)
            return DiscographyHandler.Result('Discography successfully fetched', badge_codes, token, response)
        except ValueError as e:
            Log.get().warning(e.with_traceback)
            token = self.badge_service.create_token()
            discography = self.discography_service.get_discography([])
            raise InvalidTokenError(
                badToken=event['token'],
                goodToken=self.badge_service.create_token(),
                badges=[],
                discography=discography)
        except Exception:
            Log.get().exception("DiscographyHandler.handle")
            raise InternalError()

    @classmethod
    def describe(cls):
        return HandlerDescription('discography', [
            ResourceDescription('discography', [MethodDescription(HTTPMethod.GET, [
                InternalError
            ])]),
            ResourceDescription('{token}', [MethodDescription(HTTPMethod.GET, [
                InvalidTokenError, InternalError
            ])])
        ])


def handle(event, context, *, handler: DiscographyHandler = None):
    Log.get().debug(f'handle_badges triggered with event {event}')
    handler = handler if handler else DiscographyHandler()
    return handler.handle(event, context)
