# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    float_or_none,
    unified_strdate,
)


class DctpTvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dctp\.tv/(?:#/)?filme/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://www.dctp.tv/filme/videoinstallation-fuer-eine-kaufhausfassade/',
        'info_dict': {
            'id': '95eaa4f33dad413aa17b4ee613cccc6c',
            'display_id': 'videoinstallation-fuer-eine-kaufhausfassade',
            'ext': 'flv',
            'title': 'Videoinstallation für eine Kaufhausfassade',
            'description': 'Kurzfilm',
            'upload_date': '20110407',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 71.24,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_meta(
            'DC.identifier', webpage, 'video id',
            default=None) or self._search_regex(
            r'id=["\']uuid[^>]+>([^<]+)<', webpage, 'video id')

        title = self._og_search_title(webpage)

        servers = self._download_json(
            'http://www.dctp.tv/streaming_servers/', display_id,
            note='Downloading server list', fatal=False)

        if servers:
            endpoint = next(
                server['endpoint']
                for server in servers
                if isinstance(server.get('endpoint'), compat_str) and
                'cloudfront' in server['endpoint'])
        else:
            endpoint = 'rtmpe://s2pqqn4u96e4j8.cloudfront.net/cfx/st/'

        app = self._search_regex(
            r'^rtmpe?://[^/]+/(?P<app>.*)$', endpoint, 'app')

        formats = [{
            'url': endpoint,
            'app': app,
            'play_path': 'mp4:%s_dctp_0500_4x3.m4v' % video_id,
            'page_url': url,
            'player_url': 'http://svm-prod-dctptv-static.s3.amazonaws.com/dctptv-relaunch2012-109.swf',
            'ext': 'flv',
        }]

        description = self._html_search_meta('DC.description', webpage)
        upload_date = unified_strdate(
            self._html_search_meta('DC.date.created', webpage))
        thumbnail = self._og_search_thumbnail(webpage)
        duration = float_or_none(self._search_regex(
            r'id=["\']duration_in_ms[^+]>(\d+)', webpage, 'duration',
            default=None), scale=1000)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'display_id': display_id,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'duration': duration,
        }
