# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    remove_start,
)


class VideoMegaIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:www\.)?videomega\.tv/
        (?:iframe\.php)?\?ref=(?P<id>[A-Za-z0-9]+)
        '''
    _TEST = {
        'url': 'http://videomega.tv/?ref=QR0HCUHI1661IHUCH0RQ',
        'md5': 'bf5c2f95c4c917536e80936af7bc51e1',
        'info_dict': {
            'id': 'QR0HCUHI1661IHUCH0RQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        iframe_url = 'http://videomega.tv/iframe.php?ref={0:}'.format(video_id)
        req = compat_urllib_request.Request(iframe_url)
        req.add_header('Referer', url)
        webpage = self._download_webpage(req, video_id)

        try:
            escaped_data = re.findall(r'unescape\("([^"]+)"\)', webpage)[-1]
        except IndexError:
            raise ExtractorError('Unable to extract escaped data')

        playlist = compat_urllib_parse.unquote(escaped_data)

        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', playlist, 'thumbnail', fatal=False)
        video_url = self._search_regex(r'file:\s*"([^"]+)"', playlist, 'URL')
        title = remove_start(self._html_search_regex(
            r'<title>(.*?)</title>', webpage, 'title'), 'VideoMega.tv - ')

        formats = [{
            'format_id': 'sd',
            'url': video_url,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'http_headers': {
                'Referer': iframe_url,
            },
        }
