# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_filesize,
    unified_strdate,
)


class MegavideozeuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?megavideoz\.eu/video/(?P<id>.*)(?:.*)'
    _TESTS = [
        {
            'url': 'http://megavideoz.eu/video/WM6UB919XMXH/SMPTE-Universal-Film-Leader',
            'info_dict': {
                'id': '48723',
                'ext': 'mp4',
                'duration': '10',
                'title': 'SMPTE Universal Film Leader',
            }
        }
    ]


    def _real_extract(self, url):
        tmp_video_id = self._match_id(url)

        webpage = self._download_webpage(url, tmp_video_id)

        config_php = self._html_search_regex(
            r'var cnf = \'([^\']+)\'', webpage, 'config.php url')

	configpage = self._download_webpage(config_php, tmp_video_id)

        video_id = self._html_search_regex(
            r'<mediaid>([^<]+)', configpage, 'video id')
        video_url = self._html_search_regex(
            r'<file>([^<]+)', configpage, 'video URL')
        title = self._html_search_regex(
            r'<title><!\[CDATA\[([^\]]+)', configpage, 'title')
        duration = int_or_none(self._html_search_regex(
            r'<duration>([0-9\.]+)', configpage, 'duration', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'duration': duration
        }
