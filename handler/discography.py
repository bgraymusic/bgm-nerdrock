from handler.base import HandlerBase
from discography.service import DiscographyService
from http import HTTPStatus


class DiscographyHandler(HandlerBase):
    def __init__(self, config, LOG, discography_service=None, badge_service=None):
        super().__init__(config, LOG)
        self.discography_service = discography_service if discography_service else DiscographyService(
            config, LOG, bandcamp=discography_service.bandcamp if discography_service else None,
            badge_core=badge_service.core if badge_service else None)
        self.badge_service = badge_service

    class Result(dict):
        def __init__(self, message, badges, token, discography):
            self['message'] = message
            self['badges'] = badges
            self['token'] = token
            self['discography'] = discography

    def handle(self, event, context):
        super().handle(event, context)
        try:
            token = event['token'] if 'token' in event else self.badge_service.create_token(
            )
            __, badge_codes = self.badge_service.get_badges_from_token(token)
            response = self.discography_service.get_discography(
                badge_codes, no_cache=False)
            return DiscographyHandler.Result('Discography successfully fetched', badge_codes, token, response)
        except ValueError as e:
            self.LOG.warning(e.with_traceback)
            token = self.badge_service.create_token()
            discography = self.discography_service.get_discography(
                [], no_cache=False)
            raise HandlerBase.LambdaError(HTTPStatus.UNAUTHORIZED, DiscographyHandler.Result(
                'Invalid token, creating default', [], token, discography))
        except Exception as e:
            self.LOG.exception("handlers.handle_discography")
            raise HandlerBase.LambdaError(HTTPStatus.INTERNAL_SERVER_ERROR, DiscographyHandler.Result(
                'Internal Server Error', [], event['token'] if 'token' in event else None, None), e)
