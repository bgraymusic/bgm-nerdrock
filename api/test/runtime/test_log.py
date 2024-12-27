import os
import logging
from ...runtime.log import Log


def test_log_get_default():
    os.environ.pop('log_level', None)
    log: logging.Logger = Log.get(force_new=True)
    assert log.level == logging.INFO


def test_log_warn():
    os.environ['log_level'] = 'WARNING'
    log: logging.Logger = Log.get(force_new=True)
    assert log.level == logging.WARNING
