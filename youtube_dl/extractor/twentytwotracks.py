from __future__ import unicode_literals

import re

from .common import InfoExtractor

# 22Tracks regularly replace the audio tracks that can be streamed on their
# site. The tracks usually expire after 1 months, so we can't add tests.


class TwentyTwoTracksIE(InfoExtractor):
    _VALID_URL = r'http://22tracks\.com/([a-z]+)/([a-z]+[2]*)/(\d+)'
    IE_NAME = 'TwentyTwoTracks:Tracks'

    def _extract_info(self, city, genre, track=''):
        self._base_url = "http://22tracks.com/api/"

        if track == '':
            itemid = genre
        else:
            itemid = track

        cities = self._download_json(
            self._base_url + 'cities', itemid,
            'Downloading city info', 'Cannot download city info')
        city_id = [x['id'] for x in cities if x['slug'] == city]

        genres = self._download_json(
            self._base_url + 'genres/' + str(city_id[0]), itemid,
            'Downloading genre info', 'Cannot download genre info')
        genre_id = [x['id'] for x in genres if x['slug'] == genre]

        tracks = self._download_json(
            self._base_url + 'tracks/' + str(genre_id[0]),
            itemid, 'Downloading track info', 'Cannot download track info')

        if track == '':
            return [[x['title'] for x in genres if x['slug'] == genre][0],
                    tracks]
        else:
            return [x for x in tracks if x['id'] == itemid][0]

    def _get_token(self, filename, track_id):
        token = self._download_json(
            'http://22tracks.com/token.php?desktop=true&u=%2F128%2f{0}'.format(
                filename), track_id, 'Finding download link...')

        down_url = 'http://audio.22tracks.com{0}?st={1}&e={2}'.format(
            token['filename'],
            token['st'],
            token['e'])

        return down_url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        city_id = mobj.group(1)
        genre_id = mobj.group(2)
        track_id = mobj.group(3)

        self.to_screen(':: Track ID found! - Downloading single track')

        track_info = self._extract_info(city_id, genre_id, track_id)

        download_url = self._get_token(track_info['filename'], track_id)
        title = '{0}-{1}'.format(
            track_info['artist'].strip(), track_info['title'].strip())

        return {
            'id': track_id,
            'url': download_url,
            'ext': 'mp3',
            'title': title,
            'duration': track_info['duration']
        }


class TwentyTwoTracksGenreIE(TwentyTwoTracksIE):
    _VALID_URL = r'http://22tracks\.com/([a-z]+)/([a-z]+[2]*)/?'
    IE_NAME = 'TwentyTwoTracks:Genre'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        city_id = mobj.group(1)
        genre_id = mobj.group(2)

        self.to_screen(':: Track ID not found! - Downloading entire genre')

        playlist_info = self._extract_info(city_id, genre_id)

        entries = []
        for track in playlist_info[1]:
            title = '{0}-{1}'.format(
                track['artist'].strip(), track['title'].strip())
            entries.append({
                'id': track['id'],
                'url': self._get_token(track['filename'], track['id']),
                'ext': 'mp3',
                'title': title
            })

        self.to_screen(':: Links found - Downloading Playlist')

        return {
            '_type': 'playlist',
            'id': genre_id,
            'title': playlist_info[0],
            'entries': entries
        }
