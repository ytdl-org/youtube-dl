# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request


class VideoMegaIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:www\.)?videomega\.tv/
        (?:iframe\.php|cdn\.php)?\?ref=(?P<id>[A-Za-z0-9]+)
        '''
    _TEST = {
        'url': 'http://videomega.tv/?ref=4GNA688SU99US886ANG4',
        'md5': 'bf5c2f95c4c917536e80936af7bc51e1',
        'info_dict': {
            'id': '4GNA688SU99US886ANG4',
            'ext': 'mp4',
            'title': 'BigBuckBunny_320x180',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        iframe_url = 'http://videomega.tv/cdn.php?ref=%s' % video_id
        req = compat_urllib_request.Request(iframe_url)
        req.add_header('Referer', url)
        webpage = self._download_webpage(req, video_id)

        title = self._html_search_regex(
            r'<title>(.*?)</title>', webpage, 'title')
        title = re.sub(
            r'(?:^[Vv]ideo[Mm]ega\.tv\s-\s?|\s?-\svideomega\.tv$)', '', title)
        thumbnail = self._search_regex(
            r'<video[^>]+?poster="([^"]+)"', webpage, 'thumbnail', fatal=False)
        video_url = self._search_regex(
            r'<source[^>]+?src="([^"]+)"', webpage, 'video URL')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
            'http_headers': {
                'Referer': iframe_url,
            },
        }
