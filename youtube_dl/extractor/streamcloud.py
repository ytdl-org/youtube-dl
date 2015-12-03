# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse
from ..utils import sanitized_Request


class StreamcloudIE(InfoExtractor):
    IE_NAME = 'streamcloud.eu'
    _VALID_URL = r'https?://streamcloud\.eu/(?P<id>[a-zA-Z0-9_-]+)(?:/(?P<fname>[^#?]*)\.html)?'

    _TEST = {
        'url': 'http://streamcloud.eu/skp9j99s4bpz/youtube-dl_test_video_____________-BaW_jenozKc.mp4.html',
        'md5': '6bea4c7fa5daaacc2a946b7146286686',
        'info_dict': {
            'id': 'skp9j99s4bpz',
            'ext': 'mp4',
            'title': 'youtube-dl test video  \'/\\ ä ↭',
        },
        'skip': 'Only available from the EU'
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://streamcloud.eu/%s' % video_id

        orig_webpage = self._download_webpage(url, video_id)

        fields = re.findall(r'''(?x)<input\s+
            type="(?:hidden|submit)"\s+
            name="([^"]+)"\s+
            (?:id="[^"]+"\s+)?
            value="([^"]*)"
            ''', orig_webpage)
        post = compat_urllib_parse.urlencode(fields)

        self._sleep(12, video_id)
        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        req = sanitized_Request(url, post, headers)

        webpage = self._download_webpage(
            req, video_id, note='Downloading video page ...')
        title = self._html_search_regex(
            r'<h1[^>]*>([^<]+)<', webpage, 'title')
        video_url = self._search_regex(
            r'file:\s*"([^"]+)"', webpage, 'video URL')
        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', webpage, 'thumbnail URL', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'thumbnail': thumbnail,
        }
