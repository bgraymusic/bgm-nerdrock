from ..log import Log
from ..handler_base import HandlerBase, HandlerDescription, InternalError
from .service import DatabaseService


class DatabaseHandler(HandlerBase):
    def __init__(self, *, service: DatabaseService = None):
        self.service = service if service else DatabaseService()

    class Result(dict):
        def __init__(self, message):
            self['message'] = message

    def handle(self, event, context):
        try:
            album_count = self.service.populate()
            return DatabaseHandler.Result(f'Database refreshed with {album_count} albums')
        except Exception as e:
            Log.get().exception("database_handler.handle", exc_info=e)
            raise InternalError()

    @classmethod
    def describe(cls):
        return HandlerDescription('database')


def handle(event=None, context=None, handler: DatabaseHandler = None) -> DatabaseHandler.Result:
    Log.get().debug(f'database_handler.handle triggered with event {event}')
    handler = handler if handler else DatabaseHandler()
    return handler.handle(event, context)


if __name__ == '__main__':
    handle({}, {})
