"""Simple singleton logging facility"""

import logging
from logging import Logger
import os


class Log:
    """Simple singleton logging facility"""

    _instance = None

    def __init__(self, level):
        self.log: Logger = logging.getLogger()
        self.log.setLevel(level)
        self.log.addHandler(logging.StreamHandler())

    @classmethod
    def get(cls, force_new=False) -> Logger:
        if not Log._instance or force_new:
            Log._instance = Log(os.environ.get('log_level', logging.INFO))
        return Log._instance.log
