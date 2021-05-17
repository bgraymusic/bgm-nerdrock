from handler.base import HandlerBase
from http import HTTPStatus


class RefreshCacheHandler(HandlerBase):
    def __init__(self, config, LOG, discography_service):
        super().__init__(config, LOG)
        self.discography_service = discography_service

    class Result(dict):
        def __init__(self, message):
            self['message'] = message

    def handle(self, event, context):
        super().handle(event, context)
        try:
            if self.is_refresh_trigger_event(event):
                self.discography_service.refresh_cache()
                return RefreshCacheHandler.Result('Discography cache refreshed')
            else:
                self.discography_service.trigger_cache_refresh()
                return RefreshCacheHandler.Result('Discography cache refresh triggered')
        except Exception:
            self.LOG.exception("handlers.handle_refresh_discography_cache")
            raise HandlerBase.InternalError()

    def is_refresh_trigger_event(self, event):
        return ('Records' in event and
                len(event['Records']) > 0 and
                'EventSource' in event['Records'][0] and
                event['Records'][0]['EventSource'] == 'aws:sns' and
                self.config['aws']['sns']['refreshDiscographyCache']['topic'] in event['Records'][0]['Sns']['TopicArn'])
