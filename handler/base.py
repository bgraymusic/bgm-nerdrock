import abc


class HandlerBase:

    class InvalidTokenError(Exception):
        def __init__(self, badToken, goodToken, badges, discography=None):
            super().__init__({
                'error': self.__class__.__name__,
                'badges': badges,
                'bad_token': badToken,
                'good_token': goodToken,
                'default_discography': discography
            })

    class InvalidKeyError(Exception):
        def __init__(self, badKey, token, badges):
            super().__init__({
                'error': self.__class__.__name__,
                'bad_key': badKey,
                'badges': badges,
                'token': token
            })

    class InternalError(Exception):
        def __init__(self):
            super().__init__({
                'error': self.__class__.__name__
            })

    def __init__(self, config, LOG):
        self.config = config
        self.LOG = LOG

    @abc.abstractmethod
    def handle(self, event, context):
        pass
