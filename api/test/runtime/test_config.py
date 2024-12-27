import os
import pathlib
from pytest_mock import MockerFixture
from ...runtime.config import Config


mock_data_dir = f'{pathlib.Path(__file__).parent.parent}/mock_data'
mock_config_file = 'mock_config.yml'
mock_secrets_file = 'mock_secrets.yml'
mock_secrets_bucket = 'mock_secrets_bucket'


def test_config_with_local_secrets():
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsFile'] = f'{mock_data_dir}/{mock_secrets_file}'

    config = Config.get(force_new=True)

    # something from config.yml
    assert config['aws']['account'] == '028568048704'
    # something from secrets.yml
    assert config['badges']['encryptionKey'] == 'laKNXjbnUCw7tnQHnwhSiSgkEmqsZj6B3Qx_Mqm7zr0='


def test_config_with_bucket_secrets(mocker: MockerFixture):
    os.environ['config'] = f'{mock_data_dir}/{mock_config_file}'
    os.environ['secretsBucket'] = mock_secrets_bucket
    os.environ['secretsFile'] = mock_secrets_file

    with open(f'{mock_data_dir}/{mock_secrets_file}') as secret_config_file:
        mock_s3 = mocker.MagicMock()
        mock_s3.get_object.return_value = {'Body': secret_config_file}
        mocker.patch('boto3.client', return_value=mock_s3)

        config = Config.get(force_new=True)

        # something from config.yml
        assert config['aws']['account'] == '028568048704'
        # something from secrets.yml
        assert config['badges']['encryptionKey'] == 'laKNXjbnUCw7tnQHnwhSiSgkEmqsZj6B3Qx_Mqm7zr0='
