# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class HungamaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hungama\.com/song/[^/]+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.hungama.com/song/kitni-haseen-zindagi/2931166/',
        'md5': 'a845a6d1ebd08d80c1035126d49bd6a0',
        'info_dict': {
            'id': '2931166',
            'ext': 'mp4',
            'title': 'Lucky Ali - Kitni Haseen Zindagi',
            'track': 'Kitni Haseen Zindagi',
            'artist': 'Lucky Ali',
            'album': 'Aks',
            'release_year': 2000,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'https://www.hungama.com/audio-player-data/track/%s' % video_id,
            video_id, query={'_country': 'IN'})[0]

        track = data['song_name']
        artist = data.get('singer_name')

        m3u8_url = self._download_json(
            data.get('file') or data['preview_link'],
            video_id)['response']['media_url']

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')
        self._sort_formats(formats)

        title = '%s - %s' % (artist, track) if artist else track
        thumbnail = data.get('img_src') or data.get('album_image')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'track': track,
            'artist': artist,
            'album': data.get('album_name'),
            'release_year': int_or_none(data.get('date')),
            'formats': formats,
        }
