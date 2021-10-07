from handler.base import HandlerBase


class DatabaseHandler(HandlerBase):
    def __init__(self, config, LOG, database_service):
        super().__init__(config, LOG)
        self.database_service = database_service

    class Result(dict):
        def __init__(self, message):
            self['message'] = message

    def handle(self, event, context):
        super().handle(event, context)
        try:
            self.database_service.populate()
            return DatabaseHandler.Result('Database refreshed')
        except Exception:
            self.LOG.exception("handlers.handle_refresh_database")
            raise HandlerBase.InternalError()
