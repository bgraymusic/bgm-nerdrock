import os

import pytest
from pytest_mock import MockerFixture

from ...mock_data.test_data import mock_data_dir, mock_config_file, mock_secrets_file
from ...mock_data.mock_db_contents import album_table_contents, track_table_contents
from ....runtime.config import Config
from ....runtime.discography.service import DiscographyService


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    Config.get(force_new=True)


def test_create(mocker: MockerFixture):
    setup()
    db_service = mocker.MagicMock()
    badge_core = mocker.MagicMock()

    DiscographyService(db_service=db_service, badge_core=badge_core)


def test_get_default_discography(mocker: MockerFixture):
    setup()
    db_service = mocker.MagicMock()
    db_service.queryAlbum.return_value = album_table_contents['Item']
    db_service.queryTracksFromAlbum.return_value = track_table_contents['Items']
    badge_core = mocker.MagicMock()
    badge_core.badges_spec = Config.get()['badges']['badges']
    service: DiscographyService = DiscographyService(db_service=db_service, badge_core=badge_core)

    discography = service.get_discography(badges=[])

    assert discography


def test_get_spintunes_discography(mocker: MockerFixture):
    setup()
    db_service = mocker.MagicMock()
    db_service.queryAlbum.return_value = album_table_contents['Item']
    db_service.queryTracksFromAlbum.return_value = track_table_contents['Items']
    badge_core = mocker.MagicMock()
    badge_core.badges_spec = Config.get()['badges']['badges']
    service: DiscographyService = DiscographyService(db_service=db_service, badge_core=badge_core)

    discography = service.get_discography(badges=['s'])

    assert discography


def test_get_nsfw_discography(mocker: MockerFixture):
    setup()
    db_service = mocker.MagicMock()
    db_service.queryAlbum.return_value = album_table_contents['Item']
    db_service.queryTracksFromAlbum.return_value = track_table_contents['Items']
    badge_core = mocker.MagicMock()
    badge_core.badges_spec = Config.get()['badges']['badges']
    service: DiscographyService = DiscographyService(db_service=db_service, badge_core=badge_core)

    discography = service.get_discography(badges=['w'])

    assert discography


def test_get_bad_discography(mocker: MockerFixture):
    setup()
    db_service = mocker.MagicMock()
    db_service.queryAlbum.return_value = album_table_contents['Item']
    db_service.queryTracksFromAlbum.return_value = track_table_contents['Items']
    badge_core = mocker.MagicMock()
    badge_core.badges_spec = Config.get()['badges']['badges']
    service: DiscographyService = DiscographyService(db_service=db_service, badge_core=badge_core)

    with pytest.raises(KeyError):
        service.get_discography(badges=['x'])
