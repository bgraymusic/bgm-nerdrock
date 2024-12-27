import os
from unittest.mock import call
import pytest
from pytest_mock import MockerFixture
from api.test.mock_data.test_data import (
    mock_data_dir, mock_config_file, mock_secrets_file,
    invalid_token, karaoke_key, invalid_key
)
from ....runtime.config import Config
from ....runtime.badges.service import BadgeService
from ....runtime.badges.core import BadgeCore


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_create_service(mocker: MockerFixture):
    setup()
    BadgeService(core=mocker.MagicMock())


def test_create_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.badge_codes_to_token.return_value = ']['
    service = BadgeService(core=core)

    token = service.create_token()

    call.core.badge_codes_to_token.assert_called_with([])
    assert token == ']['


def test_get_badges_from_valid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = True
    core.token_to_badge_codes.return_value = ['k']
    core.badges_spec = Config.get()['badges']['badges']
    service = BadgeService(core=core)

    badges, badge_codes = service.get_badges_from_token(']"k"[')

    call.core.is_valid_token.assert_called_with(']"k"[')
    call.core.token_to_badge_codes.assert_called_with(']"k"[')
    assert badge_codes == ['k']
    assert badges == [Config.get()['badges']['badges']['k']]


def test_get_badges_from_invalid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = False
    service = BadgeService(core=core)

    with pytest.raises(ValueError):
        service.get_badges_from_token(']"x"[')

    call.core.is_valid_token.assert_called_with(']"x"[')


def test_add_valid_badge_to_valid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = True
    core.is_valid_key.return_value = True
    core.token_to_badge_codes.return_value = []
    core.get_spec_for_key.return_value = Config.get()['badges']['badges']['k']
    core.badge_codes_to_token.return_value = ']"k"['
    service = BadgeService(core=core)

    badge_codes, token, added_code = service.add_badge_to_token('][', karaoke_key)

    call.core.is_valid_token.called_with('][')
    call.core.is_valid_key.called_with(karaoke_key)
    call.core.token_to_badge_codes.called_with('][')
    call.core.get_spec_for_key.called_with(karaoke_key)
    call.core.badge_codes_to_token.called_with(['k'])
    assert badge_codes == ['k']
    assert token == ']"k"['
    assert added_code == 'k'


def test_add_redundant_valid_badge_to_valid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = True
    core.is_valid_key.return_value = True
    core.token_to_badge_codes.return_value = ['k']
    core.get_spec_for_key.return_value = Config.get()['badges']['badges']['k']
    core.badge_codes_to_token.return_value = ']"k"['
    service = BadgeService(core=core)

    badge_codes, token, added_code = service.add_badge_to_token('][', karaoke_key)

    call.core.is_valid_token.called_with('][')
    call.core.is_valid_key.called_with(karaoke_key)
    call.core.token_to_badge_codes.called_with('][')
    call.core.get_spec_for_key.called_with(karaoke_key)
    call.core.badge_codes_to_token.called_with(['k'])
    assert badge_codes == ['k']
    assert token == ']"k"['
    assert not added_code


def test_add_invalid_badge_to_valid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = True
    core.is_valid_key.return_value = False
    service = BadgeService(core=core)

    with pytest.raises(KeyError):
        service.add_badge_to_token(']"k"[', invalid_key)

    call.core.is_valid_token.assert_called_with(']"k"[')
    call.core.is_valid_key.assert_called_with(invalid_key)


def test_add_valid_badge_to_invalid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = False
    core.is_valid_key.return_value = True
    service = BadgeService(core=core)

    with pytest.raises(ValueError):
        service.add_badge_to_token(invalid_token, karaoke_key)

    call.core.is_valid_token.assert_called_with(invalid_token)


def test_add_invalid_badge_to_invalid_token(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.is_valid_token.return_value = False
    core.is_valid_key.return_value = False
    service = BadgeService(core=core)

    with pytest.raises(ValueError):
        service.add_badge_to_token(invalid_token, invalid_key)

    call.core.is_valid_token.assert_called_with(invalid_token)


def test_internal_error(mocker: MockerFixture):
    setup()
    core: BadgeCore = mocker.MagicMock()
    core.badge_codes_to_token.side_effect = Exception()
    service = BadgeService(core=core)

    with pytest.raises(Exception):
        service.create_token()

    call.core.badge_codes_to_token.called_with([])
