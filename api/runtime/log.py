import logging
from logging import Logger
import os


class Log:
    __instance = None

    def __init__(self, level):
        self.LOG: Logger = logging.getLogger()
        self.LOG.setLevel(level)
        self.LOG.addHandler(logging.StreamHandler())

    @classmethod
    def get(cls, force_new=False) -> Logger:
        if not Log.__instance or force_new:
            Log.__instance = Log(os.environ.get('log_level', logging.INFO))
        return Log.__instance.LOG
