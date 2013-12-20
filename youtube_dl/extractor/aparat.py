#coding: utf-8

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
)


class AparatIE(InfoExtractor):
    _VALID_URL = r'^https?://(?:www\.)?aparat\.com/(?:v/|video/video/embed/videohash/)(?P<id>[a-zA-Z0-9]+)'

    _TEST = {
        u'url': u'http://www.aparat.com/v/wP8On',
        u'file': u'wP8On.mp4',
        u'md5': u'6714e0af7e0d875c5a39c4dc4ab46ad1',
        u'info_dict': {
            u"title": u"تیم گلکسی 11 - زومیت",
        },
        #u'skip': u'Extremely unreliable',
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        # Note: There is an easier-to-parse configuration at
        # http://www.aparat.com/video/video/config/videohash/%video_id
        # but the URL in there does not work
        embed_url = (u'http://www.aparat.com/video/video/embed/videohash/' +
                     video_id + u'/vt/frame')
        webpage = self._download_webpage(embed_url, video_id)

        video_urls = re.findall(r'fileList\[[0-9]+\]\s*=\s*"([^"]+)"', webpage)
        for i, video_url in enumerate(video_urls):
            req = HEADRequest(video_url)
            res = self._request_webpage(
                req, video_id, note=u'Testing video URL %d' % i, errnote=False)
            if res:
                break
        else:
            raise ExtractorError(u'No working video URLs found')

        title = self._search_regex(r'\s+title:\s*"([^"]+)"', webpage, u'title')
        thumbnail = self._search_regex(
            r'\s+image:\s*"([^"]+)"', webpage, u'thumbnail', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
        }
