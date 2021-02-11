# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    try_get,
    ExtractorError
)


class RTVSLO4DIE(InfoExtractor):
    _VALID_URL = r'https?://(?:4d|www)\.rtvslo\.si/(?:arhiv/.+|embed|4d/arhiv)/(?P<id>\d+)'
    _TEST = {
        'url': 'https://4d.rtvslo.si/arhiv/seje-odbora-za-kmetijstvo-gozdarstvo-in-prehrano/174595438',
        'md5': 'b87e5a65be2365f83eb0d24d44131d0f',
        'info_dict': {
            'id': '174595438',
            'ext': 'mp4',
            'title': 'Krajčič o tatvini sendviča',
            'thumbnail': r're:https://img.rtvslo.si/.+\.jpg',
            'timestamp': 1549999614,
            'upload_date': '20190212',
            'duration': 85
        },
    }

    def _real_extract(self, url):
        media_id = self._match_id(url)

        info_url = 'https://api.rtvslo.si/ava/getRecording/' + media_id + '?client_id=19cc0556a5ee31d0d52a0e30b0696b26'
        media_info = self._download_json(info_url, media_id)['response']

        if media_info['mediaType'] != 'video':
            raise ExtractorError('Downloading audio is not implemented for this source yet')

        # TODO: Support for audio-only links (like radio shows)
        # Instead of HLS, an mp3 URL is provided for those in ".mediaFiles[0].streams.https"

        formats = self._extract_m3u8_formats(
            media_info['addaptiveMedia']['hls'], media_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        return {
            'id': media_id,
            'title': media_info['title'],
            'description': try_get(media_info, 'description'),
            'thumbnail': media_info.get('thumbnail_sec'),
            'timestamp': unified_timestamp(media_info['broadcastDate']),
            'duration': media_info.get('duration'),
            'formats': formats,
        }
