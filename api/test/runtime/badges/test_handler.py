import os
from unittest.mock import call
import pytest
from pytest_mock import MockerFixture
from ...mock_data.test_data import (
    mock_data_dir, mock_config_file, mock_secrets_file,
    invalid_token, karaoke_key, invalid_key
)
from ....runtime.config import Config
from ....runtime.handler_base import InvalidTokenError, InvalidKeyError, InternalError, HandlerDescription
from ....runtime.badges.badges_handler import BadgesHandler, handle


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_keep_warm(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    handler = BadgesHandler(service=service)
    event = {'keep_warm': True}

    result: BadgesHandler.Result = handle(event, None, handler=handler)

    assert not result['badges']
    assert not result['token']
    assert not result['added_code']


def test_no_token(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.create_token.return_value = ']['
    handler = BadgesHandler(service=service)
    event = {}

    result: BadgesHandler.Result = handle(event, None, handler=handler)

    call.service.create_token.called()
    assert len(result['badges']) == 0
    assert result['token'] == ']['
    assert not result['added_code']


def test_valid_token_no_key(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.get_badges_from_token.return_value = (Config.get()['badges']['badges']['k'], ['k'])
    handler = BadgesHandler(service=service)
    event = {'token': ']"k"['}

    result: BadgesHandler.Result = handle(event, None, handler=handler)

    call.service.get_badges_from_token.called_with(']"k"[')
    assert result['badges'] == ['k']
    assert result['token'] == ']"k"['
    assert not result['added_code']


def test_invalid_token(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.get_badges_from_token.side_effect = ValueError()
    handler = BadgesHandler(service=service)
    event = {'token': invalid_token}

    with pytest.raises(InvalidTokenError):
        handle(event, None, handler=handler)

    call.service.get_badges_from_token.called_with(invalid_token)


def test_valid_token_valid_key(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.add_badge_to_token.return_value = (['j', 'k'], ']"k" ,"j"[', 'k')
    handler = BadgesHandler(service=service)
    event = {'token': ']"j"[', 'key': karaoke_key}

    result: BadgesHandler.Result = handle(event, None, handler=handler)

    call.service.add_badge_to_token.called_with(']"j"[', karaoke_key)
    assert result['badges'] == ['j', 'k']
    assert result['token'] == ']"k" ,"j"['
    assert result['added_code'] == 'k'


def test_valid_token_invalid_key(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.add_badge_to_token.side_effect = KeyError()
    service.get_badges_from_token.return_value = (Config.get()['badges']['badges']['j'], ['j'])
    handler = BadgesHandler(service=service)
    event = {'token': ']"j"[', 'key': invalid_key}

    with pytest.raises(InvalidKeyError):
        handle(event, None, handler=handler)

    call.service.add_badge_to_token.called_with(']"j"[', invalid_key)
    call.service.get_badges_from_token.called_with(']"j"[')


def test_internal_error(mocker: MockerFixture):
    setup()
    service = mocker.MagicMock()
    service.create_token.side_effect = Exception()
    handler = BadgesHandler(service=service)
    event = {}

    with pytest.raises(InternalError):
        handle(event, None, handler=handler)

    call.service.create_token.called()


def test_describe():
    description: HandlerDescription = BadgesHandler.describe()
    assert description.name == 'badges'
