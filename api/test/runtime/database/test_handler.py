import os
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

from ...mock_data.test_data import mock_data_dir, mock_config_file, mock_secrets_file
from ....runtime.config import Config
from ....runtime.handler_base import HandlerDescription, InternalError
from ....runtime.database.service import DatabaseService
from ....runtime.database.database_handler import handle, DatabaseHandler


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_success(mocker: MockerFixture):
    setup()
    service: DatabaseService = mocker.MagicMock()

    result: DatabaseHandler.Result = handle(None, None, handler=DatabaseHandler(service=service))

    call.service.populate.called()
    assert result['message'] == 'Database refreshed'


def test_exception(mocker: MockerFixture):
    setup()
    service: DatabaseService = mocker.MagicMock()
    service.populate.side_effect = Exception()

    with pytest.raises(InternalError):
        handle(None, None, handler=DatabaseHandler(service=service))

    call.service.populate.called()


def test_describe():
    description: HandlerDescription = DatabaseHandler.describe()
    assert description.name == 'database'
