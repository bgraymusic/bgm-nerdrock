import os
import json

import pytest
from pytest_mock import MockerFixture

from ...mock_data.test_data import mock_data_dir, mock_config_file, mock_secrets_file, mock_discography_file
from ....runtime.config import Config
from ....runtime.handler_base import HandlerDescription, InvalidTokenError, InternalError
from ....runtime.discography.discography_handler import handle, DiscographyHandler


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_keep_warm(mocker: MockerFixture):
    setup()
    discography_service = mocker.MagicMock()
    badge_service = mocker.MagicMock()
    discography_handler = DiscographyHandler(discography_service=discography_service, badge_service=badge_service)
    event = {'keep_warm': True}

    result: DiscographyHandler.Result = handle(event, None, handler=discography_handler)

    assert not result['badges']
    assert not result['token']
    assert not result['discography']


def test_no_token(mocker: MockerFixture):
    setup()
    discography_service = mocker.MagicMock()
    discography_service.get_discography.return_value = json.load(open(f'{mock_data_dir}/{mock_discography_file}'))
    badge_service = mocker.MagicMock()
    badge_service.get_badges_from_token.return_value = ([], [])
    discography_handler = DiscographyHandler(discography_service=discography_service, badge_service=badge_service)
    event = {'token': ']['}

    result: DiscographyHandler.Result = handle(event, None, handler=discography_handler)

    assert not result['badges']
    assert result['token'] == ']['
    assert len([album for album in result['discography'] if album['album_id'] == 1047117555]) > 0


def test_bad_token(mocker: MockerFixture):
    setup()
    discography_service = mocker.MagicMock()
    discography_service.get_discography.return_value = json.load(open(f'{mock_data_dir}/{mock_discography_file}'))
    badge_service = mocker.MagicMock()
    badge_service.get_badges_from_token.side_effect = ValueError()
    discography_handler = DiscographyHandler(discography_service=discography_service, badge_service=badge_service)
    event = {'token': ']"x"['}

    with pytest.raises(InvalidTokenError):
        handle(event, None, handler=discography_handler)


def test_internal_error(mocker: MockerFixture):
    setup()
    discography_service = mocker.MagicMock()
    discography_service.get_discography.return_value = json.load(open(f'{mock_data_dir}/{mock_discography_file}'))
    badge_service = mocker.MagicMock()
    badge_service.get_badges_from_token.side_effect = Exception()
    discography_handler = DiscographyHandler(discography_service=discography_service, badge_service=badge_service)
    event = {'token': ']"x"['}

    with pytest.raises(InternalError):
        handle(event, None, handler=discography_handler)


def test_describe():
    description: HandlerDescription = DiscographyHandler.describe()
    assert description.name == 'discography'
