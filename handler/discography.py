from handler.base import HandlerBase
from discography.service import DiscographyService


class DiscographyHandler(HandlerBase):
    def __init__(self, config, LOG, discography_service, badge_service):
        super().__init__(config, LOG)
        self.discography_service = discography_service if discography_service else DiscographyService(
            config, LOG, badge_core=badge_service.core if badge_service else None)
        self.badge_service = badge_service

    class Result(dict):
        def __init__(self, message, badges, token, discography):
            self['message'] = message
            self['badges'] = badges
            self['token'] = token
            self['discography'] = discography

    def handle(self, event, context):
        super().handle(event, context)
        if 'keep_warm' in event:
            return DiscographyHandler.Result('Discography handler triggered with keep_warm', None, None, None)

        try:
            token = event['token'] if 'token' in event else self.badge_service.create_token()
            __, badge_codes = self.badge_service.get_badges_from_token(token)
            response = self.discography_service.get_discography(badge_codes)
            return DiscographyHandler.Result('Discography successfully fetched', badge_codes, token, response)
        except ValueError as e:
            self.LOG.warning(e.with_traceback)
            token = self.badge_service.create_token()
            discography = self.discography_service.get_discography([])
            raise HandlerBase.InvalidTokenError(
                badToken=event['token'],
                goodToken=self.badge_service.create_token(),
                badges=[],
                discography=discography)
        except Exception as e:
            self.LOG.exception("DiscographyHandler.handle")
            raise HandlerBase.InternalError()
