# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, unified_strdate


class OlympicChannelIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?olympicchannel\.com/../video/detail/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://www.olympicchannel.com/en/video/detail/men-s-halfpipe-finals-snowboard-pyeongchang-2018-replays/',
        'info_dict': {
            'id': '1789cf09-7143-4972-b822-16210fa1a4b1',
            'ext': 'mp4',
            'title': 'Men\'s Halfpipe Finals - Snowboard | PyeongChang 2018 Replays',
            'description': 'The men\'s halfpipe finals were held at the Phoenix Snow Park on 14 February 2018.',
            'release_date': '20180308',
            'thumbnail': r're:^https?://.*',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_meta('episode_uid', webpage)
        title = self._html_search_meta('episode_title', webpage)
        formats = self._extract_m3u8_formats(self._html_search_meta('video_url', webpage), video_id, 'mp4')
        description = self._html_search_meta('episode_synopsis', webpage, fatal=False)
        release_date = unified_strdate(self._html_search_meta('content_release_date_local_utc', webpage, fatal=False))
        thumbnail = self._og_search_thumbnail(webpage)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'description': description,
            'release_date': release_date,
            'thumbnail': thumbnail,
        }
