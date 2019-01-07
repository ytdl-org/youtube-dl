# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class HungamaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)hungama\.com/song/[\w\d-]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.hungama.com/song/kitni-haseen-zindagi/2931166/',
        'md5': '396fa7e8e7e67aa25da0edc4cac9b785',
        'info_dict': {
            'id': '2931166',
            'ext': 'mp4',
            'title': 'Kitni Haseen Zindagi',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_data = self._download_json('https://www.hungama.com/audio-player-data/track/%s?_country=IN' % video_id, video_id)[0]
        title = player_data.get('song_name') or self._og_search_title(webpage)
        track_data = self._download_json(player_data['file'], video_id)
        media_url = track_data['response']['media_url']

        return {
            'id': video_id,
            'title': title,
            'formats': self._extract_m3u8_formats(media_url, video_id, ext='mp4'),
        }
