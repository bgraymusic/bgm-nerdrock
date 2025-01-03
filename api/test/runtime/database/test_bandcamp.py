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
    # response: Response = mocker.MagicMock()
    # response.raise_for_status.return_value = None
    # response.text = open(f'{mock_data_dir}/{mock_band_info_file}').read()
    # mocker.patch('requests.get', return_value=response)
    mock_response = mocker.patch('urllib.request.urlopen')
    mock_response.read.return_value = b'{"discography":[{"band_id":47474747}]}'
    bc = Bandcamp()

    band_info: dict = bc.get_band_from_bc('47474747')

    assert band_info['discography'][0]['band_id'] == 47474747


def test_get_album(mocker: MockerFixture):
    setup()
    response: Response = mocker.MagicMock()
    response.raise_for_status.return_value = None
    response.text = open(f'{mock_data_dir}/{mock_album_info_file}').read()
    mocker.patch('requests.get', return_value=response)
    bc = Bandcamp()

    album_info: dict = bc.get_album_from_bc('47474747')

    assert album_info['album_id'] == valid_album_id


def test_get_track(mocker: MockerFixture):
    setup()
    response: Response = mocker.MagicMock()
    response.raise_for_status.return_value = None
    response.text = open(f'{mock_data_dir}/{mock_track_info_file}').read()
    mocker.patch('requests.get', return_value=response)
    bc = Bandcamp()

    track_info: dict = bc.get_track_from_bc('47474747')

    assert track_info['track_id'] == valid_track_id
