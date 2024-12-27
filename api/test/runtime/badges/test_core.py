import os
import pytest
from pytest_mock import MockerFixture

from api.test.mock_data.test_data import (
    mock_data_dir, mock_config_file, mock_secrets_file,
    karaoke_key, invalid_key
)
from ....runtime.config import Config
from ....runtime.badges.core import BadgeCore


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def encryption_side_effect(input: str):
    return input[::-1]


def test_create(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    core = BadgeCore(cipher=cipher)
    assert core.badges_spec == Config.get()['badges']['badges']
    assert core.encryption_key == Config.get()['badges']['encryptionKey']


def test_create_with_both_key_and_cipher(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    encryption_key = '1234567890'
    with pytest.raises(TypeError):
        BadgeCore(encryption_key=encryption_key, cipher=cipher)


def test_create_with_unencodable_key(mocker: MockerFixture):
    setup()
    encryption_key = mocker.MagicMock()
    encryption_key.encode.side_effect = UnicodeEncodeError('utf-8', str(encryption_key), 0, 47, 'Bad encryption key')
    with pytest.raises(UnicodeEncodeError):
        BadgeCore(encryption_key=encryption_key)


def test_create_empty_token(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    cipher.encrypt.side_effect = encryption_side_effect
    core = BadgeCore(cipher=cipher)
    token = core.badge_codes_to_token([])
    assert token == core.pad_string_to_multiple_of_16('[]')[::-1]


def test_create_sfw_token(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    cipher.encrypt.side_effect = lambda s: s[::-1]
    core = BadgeCore(cipher=cipher)
    token = core.badge_codes_to_token(['w'])
    assert token == core.pad_string_to_multiple_of_16('["w"]')[::-1]


def test_valid_token(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    cipher.decrypt.side_effect = encryption_side_effect
    core = BadgeCore(cipher=cipher)
    token = ']"j"['
    assert core.is_valid_token(token)


def test_invalid_token(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    cipher.decrypt.side_effect = Exception()
    core = BadgeCore(cipher=cipher)
    token = ']"j"['
    assert not core.is_valid_token(token)


def test_valid_token_bad_key(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    cipher.decrypt.side_effect = encryption_side_effect
    core = BadgeCore(cipher=cipher)
    token = ']"x"['
    assert not core.is_valid_token(token)


def test_valid_key(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    core = BadgeCore(cipher=cipher)
    assert core.is_valid_key(karaoke_key)


def test_invalid_key(mocker: MockerFixture):
    setup()
    cipher = mocker.MagicMock()
    core = BadgeCore(cipher=cipher)
    assert not core.is_valid_key(invalid_key)
