from handler.base import HandlerBase
from http import HTTPStatus


class BadgesHandler(HandlerBase):
    def __init__(self, config, LOG, badge_service=None):
        super().__init__(config, LOG)
        self.badge_service = badge_service

    class Result(dict):
        def __init__(self, message, badges, token):
            self['message'] = message
            self['badges'] = badges
            self['token'] = token

    def handle(self, event, context):
        super().handle(event, context)
        if 'token' not in event:
            return BadgesHandler.Result('New, empty token created', [], self.badge_service.create_token())
        elif 'key' not in event:
            try:
                __, badgeCodes = self.badge_service.get_badges_from_token(
                    event['token'])
                return BadgesHandler.Result(f'Token {event["token"]} is valid', badgeCodes, event['token'])
            except ValueError as e:
                self.LOG.warning(e.with_traceback)
                raise HandlerBase.LambdaError(HTTPStatus.UNAUTHORIZED, BadgesHandler.Result(
                    'Invalid input token', [], self.badge_service.create_token()))
        else:
            try:
                badges, token = self.badge_service.add_badge_to_token(
                    event['token'], event['key'])
                return BadgesHandler.Result('Badge added to token', badges, token)
            except ValueError as e:
                self.LOG.warning(e.with_traceback)
                raise HandlerBase.LambdaError(HTTPStatus.UNAUTHORIZED, BadgesHandler.Result(
                    'Invalid input token', [], self.badge_service.create_token()))
            except KeyError as e:
                self.LOG.warning(e.with_traceback)
                __, badgeCodes = self.badge_service.get_badges_from_token(
                    event['token'])
                raise HandlerBase.LambdaError(HTTPStatus.BAD_REQUEST, BadgesHandler.Result(
                    'Invalid badge key', badgeCodes, event['token']))
