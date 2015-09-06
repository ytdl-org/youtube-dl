# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)


class FilehootIE(InfoExtractor):
    IE_NAME = 'filehoot.com'
    _VALID_URL = r'https?://filehoot\.com/(?P<id>[a-zA-Z0-9_-]+)(\.html)?'

    _TEST = {
        'url': 'http://filehoot.com/3ivfabn7573c.html',
        'info_dict': {
            'id': '3ivfabn7573c',
            'ext': 'mp4',
            'title': 'youtube-dl test video \'äBaW_jenozKc.mp4.mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://filehoot.com/%s' % video_id

        orig_webpage = self._download_webpage(url, video_id)

        fields = re.findall(r'''(?x)<input\s+
            [^<]+
            name="([^"]+)"\s+
            value="([^"]*)"
            ''', orig_webpage)

        fields.pop(0)
        fields.pop(0)

        post = compat_urllib_parse.urlencode(fields)
        req = compat_urllib_request.Request(url, post)

        webpage = self._download_webpage(req, video_id, note='Downloading video page ...')
        title = self._html_search_regex(r'<td nowrap[^>]*>([^<]+)<', webpage, 'title')
        video_url = self._search_regex(r'file:\s*"([^"]+)"', webpage, 'video URL')
        thumbnail = self._search_regex(r'image:\s*"([^"]+)"', webpage, 'thumbnail URL', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
        }
