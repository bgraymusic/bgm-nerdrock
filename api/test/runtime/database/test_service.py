import os
import json
from unittest.mock import call

from pytest_mock import MockerFixture

from ...mock_data.test_data import (
    mock_data_dir, mock_config_file, mock_secrets_file, mock_album_info_file, mock_track_info_yml
)
from ...mock_data.mock_db_contents import album_table_contents, track_table_contents
from ....runtime.config import Config
from ....runtime.database.service import DatabaseService


def setup():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'
    os.environ['trackInfo'] = f'{mock_data_dir}/{mock_track_info_yml}'
    Config.get(force_new=True)

    
def test_create(mocker: MockerFixture):
    setup()
    album_table = mocker.MagicMock()
    track_table = mocker.MagicMock()
    bandcamp = mocker.MagicMock()

    service = DatabaseService(album_table=album_table, track_table=track_table, bandcamp=bandcamp)

    assert len(service.album_ids) == 7


def test_clear(mocker: MockerFixture):
    setup()
    album_table = mocker.MagicMock()
    album_table.scan.return_value = album_table_contents
    batch_writer = mocker.MagicMock()
    batch_writer.delete_item.return_value = mocker.MagicMock()
    album_table.batch_writer.return_value = batch_writer

    track_table = mocker.MagicMock()
    track_table.scan.return_value = track_table_contents

    service = DatabaseService(album_table=album_table, track_table=track_table, bandcamp=mocker.MagicMock())

    service.clear()

    for album in album_table_contents['Items']:
        call.batch_writer.delete_item.assert_called_with(Key={'album_id': album['album_id']})


def test_populate(mocker: MockerFixture):
    setup()
    album_table = mocker.MagicMock()
    track_table = mocker.MagicMock()
    bandcamp = mocker.MagicMock()

    bandcamp.get_album_from_bc.return_value = json.load(open(f'{mock_data_dir}/{mock_album_info_file}'))

    album_batch_writer = mocker.MagicMock()
    album_batch_writer.put_item.return_value = mocker.MagicMock()
    album_table.batch_writer.return_value = album_batch_writer

    track_batch_writer = mocker.MagicMock()
    track_batch_writer.put_item.return_value = mocker.MagicMock()
    track_table.batch_writer.return_value = track_batch_writer

    service = DatabaseService(album_table=album_table, track_table=track_table, bandcamp=bandcamp)

    service.populate()

    call.album_batch_writer.put_item.assert_called_with(Item=bandcamp.get_album_from_bc.return_value)
    for track in bandcamp.get_album_from_bc.return_value:
        call.track_batch_writer.put_item.assert_called_with(Item=track)


def test_query_album(mocker: MockerFixture):
    setup()
    album_table = mocker.MagicMock()
    album_table.get_item.return_value = album_table_contents
    track_table = mocker.MagicMock()
    bandcamp = mocker.MagicMock()
    service = DatabaseService(album_table=album_table, track_table=track_table, bandcamp=bandcamp)

    album_data = service.queryAlbum(47474747)

    assert album_data['album_id'] == 1047117555


def test_query_tracks_from_album(mocker: MockerFixture):
    setup()
    album_table = mocker.MagicMock()
    track_table = mocker.MagicMock()
    track_table.query.return_value = track_table_contents
    bandcamp = mocker.MagicMock()
    service = DatabaseService(album_table=album_table, track_table=track_table, bandcamp=bandcamp)

    track_data = service.queryTracksFromAlbum(47474747, False)

    assert track_data[0]['track_id'] == 10211934
