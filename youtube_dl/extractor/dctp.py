# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_strdate


class DctpTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dctp\.tv/(#/)?filme/(?P<id>.+?)/$'
    _TEST = {
        'url': 'http://www.dctp.tv/filme/videoinstallation-fuer-eine-kaufhausfassade/',
        'md5': '174dd4a8a6225cf5655952f969cfbe24',
        'info_dict': {
            'id': '95eaa4f33dad413aa17b4ee613cccc6c',
            'display_id': 'videoinstallation-fuer-eine-kaufhausfassade',
            'ext': 'mp4',
            'title': 'Videoinstallation für eine Kaufhausfassade',
            'description': 'Kurzfilm',
            'upload_date': '20110407',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        object_id = self._html_search_meta('DC.identifier', webpage)

        servers_json = self._download_json(
            'http://www.dctp.tv/elastic_streaming_client/get_streaming_server/',
            video_id, note='Downloading server list')
        server = servers_json[0]['server']
        m3u8_path = self._search_regex(
            r'\'([^\'"]+/playlist\.m3u8)"', webpage, 'm3u8 path')
        formats = self._extract_m3u8_formats(
            'http://%s%s' % (server, m3u8_path), video_id, ext='mp4',
            entry_protocol='m3u8_native')

        title = self._og_search_title(webpage)
        description = self._html_search_meta('DC.description', webpage)
        upload_date = unified_strdate(
            self._html_search_meta('DC.date.created', webpage))
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': object_id,
            'title': title,
            'formats': formats,
            'display_id': video_id,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
        }
