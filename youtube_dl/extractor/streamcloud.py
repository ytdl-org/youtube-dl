# coding: utf-8
import re
import time

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
)


class StreamcloudIE(InfoExtractor):
    IE_NAME = u'streamcloud.eu'
    _VALID_URL = r'https?://streamcloud\.eu/(?P<id>[a-zA-Z0-9_-]+)/(?P<fname>[^#?]*)\.html'

    _TEST = {
        u'url': u'http://streamcloud.eu/skp9j99s4bpz/youtube-dl_test_video_____________-BaW_jenozKc.mp4.html',
        u'file': u'skp9j99s4bpz.mp4',
        u'md5': u'6bea4c7fa5daaacc2a946b7146286686',
        u'info_dict': {
            u'title': u'youtube-dl test video  \'/\\ ä ↭',
            u'duration': 9,
        },
        u'skip': u'Only available from the EU'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        orig_webpage = self._download_webpage(url, video_id)

        fields = re.findall(r'''(?x)<input\s+
            type="(?:hidden|submit)"\s+
            name="([^"]+)"\s+
            (?:id="[^"]+"\s+)?
            value="([^"]*)"
            ''', orig_webpage)
        post = compat_urllib_parse.urlencode(fields)

        self.to_screen('%s: Waiting for timeout' % video_id)
        time.sleep(12)
        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
        }
        req = compat_urllib_request.Request(url, post, headers)

        webpage = self._download_webpage(
            req, video_id, note=u'Downloading video page ...')
        title = self._html_search_regex(
            r'<h1[^>]*>([^<]+)<', webpage, u'title')
        video_url = self._search_regex(
            r'file:\s*"([^"]+)"', webpage, u'video URL')
        duration_str = self._search_regex(
            r'duration:\s*"?([0-9]+)"?', webpage, u'duration', fatal=False)
        duration = None if duration_str is None else int(duration_str)
        thumbnail = self._search_regex(
            r'image:\s*"([^"]+)"', webpage, u'thumbnail URL', fatal=False)

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'duration': duration,
            'thumbnail': thumbnail,
        }
