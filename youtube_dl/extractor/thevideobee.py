# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    urlencode_postdata,
)


class TheVideoBeeIE(InfoExtractor):
    IE_NAME = 'thevideobee.to'
    _VALID_URL = r'https?:\/\/(www\.)?thevideobee\.to\/(?P<id>[a-zA-Z0-9-]+)(\.html)?'
    _TEST = {
        'url': 'http://thevideobee.to/wuqosqufmqv3',
        'md5': 'ffa2f1484d99548226876554ec808f00',
        'info_dict': {
            'id': 'wuqosqufmqv3',
            'ext': 'mp4',
            'title': 'Most Crazy Complex Pranks',
            'thumbnail': 'http://fsc.thevideobee.to/i/01/00000/wuqosqufmqv3.jpg'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = 'http://thevideobee.to/%s' % video_id

        orig_webpage = self._download_webpage(url, video_id)

        fields = re.findall(
            r'''(?x)<input\s+
            type="hidden"\s+
            name="(.*?)"\s+
            value="(.*?)"''',
            orig_webpage
        )

        post = urlencode_postdata(fields)

        self._sleep(8, video_id)

        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        req = sanitized_Request(url, post, headers)

        webpage = self._download_webpage(req, video_id, note='Downloading video page ...')

        title = self._html_search_regex(r'<h1>([^<]+)<\/h1>', webpage, 'title')
        video_url = self._search_regex(r'file:\s*"([^"]+\.mp4)', webpage, 'video URL')
        thumbnail = self._search_regex(r'image:\s*"(.*?)"', webpage, 'thumbnail URL', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'thumbnail': thumbnail
        }
