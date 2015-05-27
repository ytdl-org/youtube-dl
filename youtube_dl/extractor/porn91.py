# encoding: utf-8
from __future__ import unicode_literals

import re

from ..compat import compat_urllib_parse
from .common import InfoExtractor
from ..utils import ExtractorError


class Porn91IE(InfoExtractor):
    IE_NAME = '91porn'
    _VALID_URL = r'(?:https?://)(?:www\.|)91porn\.com/.+?\?viewkey=(?P<id>[\w\d]+)'

    _TEST = {
            'url': 'http://91porn.com/view_video.php?viewkey=7e42283b4f5ab36da134',
            'md5': '6df8f6d028bc8b14f5dbd73af742fb20',
            'info_dict': {
                'id': '7e42283b4f5ab36da134',
                'title': '18岁大一漂亮学妹，水嫩性感，再爽一次！',
                'ext': 'mp4'
            }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        url = 'http://91porn.com/view_video.php?viewkey=%s' % video_id
        self._set_cookie('91porn.com', 'language', 'cn_CN')
        webpage = self._download_webpage(url, video_id, "get HTML content")
        title = self._search_regex(
            r'<div id="viewvideo-title">(?P<title>.+?)</div>',
            webpage, 'title', flags=re.DOTALL)
        assert title
        title = title.replace('\n', '')

        # get real url
        n1 = self._search_regex(
            r'so.addVariable\(\'file\',\'(?P<n1>\d+)\'', webpage, 'n1')
        n2 = self._search_regex(
            r'so.addVariable\(\'seccode\',\'(?P<n2>.+?)\'', webpage, 'n2')
        n3 = self._search_regex(
            r'so.addVariable\(\'max_vid\',\'(?P<n3>\d+)\'', webpage, 'n3')
        if not (n1 and n2 and n3):
            raise ExtractorError("You are Blocked by Server.")
        url_params = compat_urllib_parse.urlencode({
            'VID': n1,
            'mp4': '1',
            'seccode': n2,
            'max_vid': n3,
        })
        t_url = 'http://91porn.com/getfile.php?' + url_params
        info_cn = self._download_webpage(t_url, video_id, "get real video_url")
        video_url = self._search_regex(r'file=(?P<url>http.+?)&', info_cn, 'url')

        # construct info
        info = {
            'id': video_id,
            'title': title,
            'url': video_url,
        }

        return info
