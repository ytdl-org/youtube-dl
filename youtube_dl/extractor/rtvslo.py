# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_timestamp,
    try_get, ExtractorError
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
        video_id = self._match_id(url)

        embed_url = 'https://4d.rtvslo.si/embed/' + video_id
        embed_html = self._download_webpage(embed_url, video_id)

        client_id = self._search_regex(r'\[\'client\'\] = "(.+?)";', embed_html, 'clientId')

        info_url = 'https://api.rtvslo.si/ava/getRecordingDrm/' + video_id + '?client_id=' + client_id
        video_info = self._download_json(info_url, video_id)['response']

        if video_info["mediaType"] != "video":
            raise ExtractorError("Downloading audio is not implemented for this source yet")

        jwt = video_info['jwt']

        media_info_url = 'https://api.rtvslo.si/ava/getMedia/' + video_id + '?client_id=' + client_id + '&jwt=' + jwt
        media_info = self._download_json(media_info_url, video_id)['response']

        # TODO: Support for audio-only links (like radio shows)
        # Instead of HLS, an mp3 URL is provided for those in ".mediaFiles[0].streams.https"

        formats = self._extract_m3u8_formats(
            media_info['addaptiveMedia']['hls'], video_id, 'mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')

        return {
            'id': video_id,
            'title': video_info['title'],
            'description': try_get(video_info, 'description'),
            'thumbnail': video_info.get('thumbnail_sec'),
            'timestamp': unified_timestamp(video_info['broadcastDate']),
            'duration': video_info.get('duration'),
            'formats': formats,
        }
