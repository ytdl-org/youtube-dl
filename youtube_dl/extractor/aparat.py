# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
)


class AparatIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?aparat\.com/(?:v/|video/video/embed/videohash/)(?P<id>[a-zA-Z0-9]+)'

    _TEST = {
        'url': 'http://www.aparat.com/v/wP8On',
        'md5': '6714e0af7e0d875c5a39c4dc4ab46ad1',
        'info_dict': {
            'id': 'wP8On',
            'ext': 'mp4',
            'title': 'تیم گلکسی 11 - زومیت',
            'age_limit': 0,
        },
        # 'skip': 'Extremely unreliable',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Note: There is an easier-to-parse configuration at
        # http://www.aparat.com/video/video/config/videohash/%video_id
        # but the URL in there does not work
        embed_url = ('http://www.aparat.com/video/video/embed/videohash/' +
                     video_id + '/vt/frame')
        webpage = self._download_webpage(embed_url, video_id)

        video_urls = [video_url.replace('\\/', '/') for video_url in re.findall(
            r'(?:fileList\[[0-9]+\]\s*=|"file"\s*:)\s*"([^"]+)"', webpage)]
        for i, video_url in enumerate(video_urls):
            req = HEADRequest(video_url)
            res = self._request_webpage(
                req, video_id, note='Testing video URL %d' % i, errnote=False)
            if res:
                break
        else:
            raise ExtractorError('No working video URLs found')

        title = self._search_regex(r'\s+title:\s*"([^"]+)"', webpage, 'title')
        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'age_limit': self._family_friendly_search(webpage),
        }
