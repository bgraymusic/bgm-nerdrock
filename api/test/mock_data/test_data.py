import pathlib

mock_data_dir = f'{pathlib.Path(__file__).parent}'
mock_config_file = 'mock_config.yml'
mock_secrets_file = 'mock_secrets.yml'
mock_band_info_file = 'mock_band_info.json'
mock_album_info_file = 'mock_album_info.json'
mock_track_info_file = 'mock_track_info.json'
mock_track_info_yml = 'mock_track_info.yml'
mock_discography_file = 'mock_discography.json'

encryptionKey = 'laKNKjbnUCw7tnQHnwhSi5gkEmqsZj6B3Qx_Mqm7zro='

valid_empty_token = 'gAAAAABnYH5addGdQO46eVrPJ3SFd71Sk1xJKTaGh0xuk05bKx4M393VjvC3b6X5C-RUETl3bG5FO32mfGfsiv5287Z9OPK8S8A1gqqyJ5fVOfEUPxIzvgs='
valid_karaoke_token = 'gAAAAABnYJUuylpohomIm98DrgT4tu550sON3T_RUrh9WH-Z9BcbEq54-2Wodk6qzSiSvukIrQzCi-K7_sGZfJGEoXu1WbIu2b_n2t_alulq7ksCxresCAQ='
valid_token_bad_code = 'gAAAAABnYIR24lMWAihYa5cnWCoWxPjB8Cw6evjPEZVTrAouebjoB3WIdCzjDseB67vIRGrRcEe_n_uOYHoCuTpll9C3RJQ7Ev__TLI5C5an_rRWf6I8NqY='
invalid_token = 'gAAAAABnYH5addGdQO46eVrPJ3SFd71Sk1xJKTaGh0xuk05bKx4M393VjhgYrdKia-RUETl3bG5FO32mfGfsiv5287Z9OPK8S8A1gqqyJ5fVOfEUPxIzvgs='
karaoke_key = 'karaokey'
invalid_key = 'zaboomafoo'

valid_band_id = 230945364
valid_album_id = 1047117555
valid_track_id = 10211934
