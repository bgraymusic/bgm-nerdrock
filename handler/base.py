import abc


class HandlerBase:

    class LambdaError(Exception):
        def __init__(self, status, result, exc=None):
            result['errorCode'] = status
            result['message'] = f'[{status}] {result["message"]}'
            result['exception'] = exc
            super().__init__(result)

    def __init__(self, config, LOG):
        self.config = config
        self.LOG = LOG

    @abc.abstractmethod
    def handle(self, event, context):
        pass
