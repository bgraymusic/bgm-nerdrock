"""Entry point and handler for the /api/badges endpoint"""

from http import HTTPMethod
from ..log import Log
from ..handler_base import (
    HandlerBase, HandlerDescription,
    InvalidTokenError, InvalidKeyError, InternalError,
    ResourceDescription, MethodDescription
)
from .service import BadgeService


class BadgesHandler(HandlerBase):
    """Handler definition for the /api/badges endpoint, including keep_warm"""

    def __init__(self, *, service: BadgeService | None = None) -> None:
        self.service = service if service else BadgeService()

    class Result(dict):
        def __init__(self, message, badges, token, addedCode=None):
            self['message'] = message
            self['badges'] = badges
            self['token'] = token
            self['added_code'] = addedCode

    def handle(self, event, context) -> Result:
        if 'keep_warm' in event:
            return BadgesHandler.Result('Badges handler triggered with keep_warm', None, None)

        try:
            if 'token' not in event:
                return BadgesHandler.Result('New, empty token created', [], self.service.create_token())
            elif 'key' not in event:
                _, badge_codes = self.service.get_badges_from_token(
                    event['token'])
                return BadgesHandler.Result(f'Token {event['token']} is valid', badge_codes, event['token'])
            else:
                badges, token, added_code = self.service.add_badge_to_token(
                    event['token'], event['key'])
                return BadgesHandler.Result('Badge added to token', badges, token, added_code)
        except ValueError as e:
            Log.get().warning(e.with_traceback)
            raise InvalidTokenError(
                badToken=event['token'],
                goodToken=self.service.create_token(),
                badges=[]) from e
        except KeyError as e:
            Log.get().warning(e.with_traceback)
            _, badge_codes = self.service.get_badges_from_token(
                event['token'])
            raise InvalidKeyError(
                badKey=event['key'],
                token=event['token'],
                badges=badge_codes) from e
        except Exception as e:
            Log.get().exception('BadgesHandler.handle')
            raise InternalError() from e

    @classmethod
    def describe(cls) -> HandlerDescription:
        return HandlerDescription(cls.__module__.split('.')[-2], [
            ResourceDescription(
                'badges',
                [MethodDescription(HTTPMethod.GET, [InternalError])]),
            ResourceDescription(
                '{token}',
                [MethodDescription(HTTPMethod.GET, [InvalidTokenError, InternalError])]),
            ResourceDescription(
                '{key}',
                [MethodDescription(HTTPMethod.GET, [InvalidTokenError, InvalidKeyError, InternalError])])
        ], keep_warm=True)


def handle(event, context, *, handler: BadgesHandler | None = None) -> BadgesHandler.Result:
    Log.get().debug(f'handle_badges triggered with event {event}')
    handler = handler if handler else BadgesHandler()
    return handler.handle(event, context)
