import os
from requests import Response
from pytest_mock import MockerFixture
from ...mock_data.test_data import (
    mock_data_dir, mock_config_file, mock_secrets_file,
    mock_band_info_file, mock_album_info_file, mock_track_info_file,
    valid_band_id, valid_album_id, valid_track_id
)
from ....runtime.config import Config
from ....runtime.database.bandcamp import Bandcamp


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_get_band(mocker: MockerFixture):
    setup()
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = b'{"discography":[{"band_id":47474747}]}'
    mock_response.__enter__.return_value = mock_response
    mocker.patch('urllib.request.urlopen').return_value = mock_response
    bc = Bandcamp()

    band_info: dict = bc.get_band_from_bc('47474747')

    assert band_info['discography'][0]['band_id'] == 47474747


def test_get_album(mocker: MockerFixture):
    setup()
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = b'{"album_id":47474747}'
    mock_response.__enter__.return_value = mock_response
    mocker.patch('urllib.request.urlopen').return_value = mock_response
    bc = Bandcamp()

    album_info: dict = bc.get_album_from_bc('47474747')

    assert album_info['album_id'] == 47474747


def test_get_track(mocker: MockerFixture):
    setup()
    mock_response = mocker.MagicMock()
    mock_response.read.return_value = b'{"track_id":47474747}'
    mock_response.__enter__.return_value = mock_response
    mocker.patch('urllib.request.urlopen').return_value = mock_response
    bc = Bandcamp()

    track_info: dict = bc.get_track_from_bc('47474747')

    assert track_info['track_id'] == 47474747
