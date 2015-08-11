from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

# 22Tracks regularly replace the audio tracks that can be streamed on their
# site. The tracks usually expire after 1 months, so we can't add tests.


class TwentyTwoTracksIE(InfoExtractor):
    _VALID_URL = r'https?://22tracks\.com/(?P<city>[a-z]+)/(?P<genre>[\da-z]+)/(?P<id>\d+)'
    IE_NAME = '22tracks:track'

    _API_BASE = 'http://22tracks.com/api'

    def _extract_info(self, city, genre_name, track_id=None):
        item_id = track_id if track_id else genre_name

        cities = self._download_json(
            '%s/cities' % self._API_BASE, item_id,
            'Downloading cities info',
            'Unable to download cities info')
        city_id = [x['id'] for x in cities if x['slug'] == city][0]

        genres = self._download_json(
            '%s/genres/%s' % (self._API_BASE, city_id), item_id,
            'Downloading %s genres info' % city,
            'Unable to download %s genres info' % city)
        genre = [x for x in genres if x['slug'] == genre_name][0]
        genre_id = genre['id']

        tracks = self._download_json(
            '%s/tracks/%s' % (self._API_BASE, genre_id), item_id,
            'Downloading %s genre tracks info' % genre_name,
            'Unable to download track info')

        return [x for x in tracks if x['id'] == item_id][0] if track_id else [genre['title'], tracks]

    def _get_track_url(self, filename, track_id):
        token = self._download_json(
            'http://22tracks.com/token.php?desktop=true&u=/128/%s' % filename,
            track_id, 'Downloading token', 'Unable to download token')
        return 'http://audio.22tracks.com%s?st=%s&e=%d' % (token['filename'], token['st'], token['e'])

    def _extract_track_info(self, track_info, track_id):
        download_url = self._get_track_url(track_info['filename'], track_id)
        title = '%s - %s' % (track_info['artist'].strip(), track_info['title'].strip())
        return {
            'id': track_id,
            'url': download_url,
            'ext': 'mp3',
            'title': title,
            'duration': int_or_none(track_info.get('duration')),
            'timestamp': int_or_none(track_info.get('published_at') or track_info.get('created'))
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        city = mobj.group('city')
        genre = mobj.group('genre')
        track_id = mobj.group('id')

        track_info = self._extract_info(city, genre, track_id)
        return self._extract_track_info(track_info, track_id)


class TwentyTwoTracksGenreIE(TwentyTwoTracksIE):
    _VALID_URL = r'https?://22tracks\.com/(?P<city>[a-z]+)/(?P<genre>[\da-z]+)/?$'
    IE_NAME = '22tracks:genre'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        city = mobj.group('city')
        genre = mobj.group('genre')

        genre_title, tracks = self._extract_info(city, genre)

        entries = [
            self._extract_track_info(track_info, track_info['id'])
            for track_info in tracks]

        return self.playlist_result(entries, genre, genre_title)
