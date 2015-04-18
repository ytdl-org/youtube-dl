# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none,
    xpath_text,
)


class MegaVideozIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?megavideoz\.eu/video/(?P<id>[^/]+)(?:/(?P<display_id>[^/]+))?'
    _TEST = {
        'url': 'http://megavideoz.eu/video/WM6UB919XMXH/SMPTE-Universal-Film-Leader',
        'info_dict': {
            'id': '48723',
            'display_id': 'SMPTE-Universal-Film-Leader',
            'ext': 'mp4',
            'title': 'SMPTE Universal Film Leader',
            'thumbnail': 're:https?://.*?\.jpg',
            'duration': 10.93,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        if any(p in webpage for p in ('>Video Not Found<', '>404 Error<')):
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        config = self._download_xml(
            self._search_regex(
                r"var\s+cnf\s*=\s*'([^']+)'", webpage, 'cnf url'),
            display_id)

        video_url = xpath_text(config, './file', 'video url', fatal=True)
        title = xpath_text(config, './title', 'title', fatal=True)
        thumbnail = xpath_text(config, './image', 'thumbnail')
        duration = float_or_none(xpath_text(config, './duration', 'duration'))
        video_id = xpath_text(config, './mediaid', 'video id') or video_id

        return {
            'id': video_id,
            'display_id': display_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration
        }
