# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    remove_start,
)


class VideoMegaIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:www\.)?videomega\.tv/
        (?:iframe\.php)?\?ref=(?P<id>[A-Za-z0-9]+)
        '''
    _TEST = {
        'url': 'http://videomega.tv/?ref=GKeGPVedBe',
        'md5': '240fb5bcf9199961f48eb17839b084d6',
        'info_dict': {
            'id': 'GKeGPVedBe',
            'ext': 'mp4',
            'title': 'XXL - All Sports United',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://videomega.tv/iframe.php?ref={0:}'.format(video_id)
        webpage = self._download_webpage(url, video_id)

        escaped_data = self._search_regex(
            r'unescape\("([^"]+)"\)', webpage, 'escaped data')
        playlist = compat_urllib_parse.unquote(escaped_data)

        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', playlist, 'thumbnail', fatal=False)
        url = self._search_regex(r'file:\s*"([^"]+)"', playlist, 'URL')
        title = remove_start(self._html_search_regex(
            r'<title>(.*?)</title>', webpage, 'title'), 'VideoMega.tv - ')

        formats = [{
            'format_id': 'sd',
            'url': url,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
