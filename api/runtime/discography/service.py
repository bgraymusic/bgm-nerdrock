from ..config import Config
from ..log import Log
from ..badges.core import BadgeCore
from ..database.service import DatabaseService


class DiscographyService:

    def __init__(self, *, db_service: DatabaseService = None, badge_core: BadgeCore = None):
        self.badge_core = badge_core if badge_core else BadgeCore()
        self.db_service = db_service if db_service else DatabaseService()

    def get_discography(self, badges):
        album_ids = self.get_album_ids_for_badges(badges)
        Log.get().debug(f'Fetching discography for albums: {album_ids}')
        return self.get_selected_albums(album_ids, 'w' in badges)

    def get_selected_albums(self, album_ids, sfw=False):
        albums = []
        for album_id in album_ids:
            album = self.db_service.queryAlbum(int(album_id))
            tracks = self.db_service.queryTracksFromAlbum(int(album_id),
                                                          album_id in Config.get()['albums']['forwardSorted'])
            if sfw:
                album['tracks'] = list(filter(lambda track: 'nsfw' not in track or not track['nsfw'], tracks))
            else:
                album['tracks'] = tracks
            albums.append(album)
        return albums

    def get_album_ids_for_badges(self, badges):
        album_ids = Config.get()['badges']['defaultAlbumIDs'].copy()
        for badge_key in badges:
            spec = self.badge_core.badges_spec[badge_key]
            if spec and 'albumIDs' in spec and len(spec['albumIDs']) > 0:
                album_ids += spec['albumIDs']
        return album_ids
