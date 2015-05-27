# encoding: utf-8
from __future__ import unicode_literals

import re
import json

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
        title = re.search(
            r'<div id="viewvideo-title">(.+?)</div>',
            webpage,
            re.DOTALL)
        assert title
        title = title.group(1).replace('\n', '')

        # get real url
        n1 = re.search(r'so.addVariable\(\'file\',\'(\d+)\'', webpage)
        n2 = re.search(r'so.addVariable\(\'seccode\',\'(.+?)\'', webpage)
        n3 = re.search(r'so.addVariable\(\'max_vid\',\'(\d+)\'', webpage)
        if not (n1 and n2 and n3):
            raise ExtractorError("You are Blocked by Server.")

        url_params = compat_urllib_parse.urlencode({
            'VID': n1.group(1),
            'mp4': '1',
            'seccode': n2.group(1),
            'max_vid': n3.group(1),
        })
        t_url = 'http://91porn.com/getfile.php?' + url_params
        info_cn = self._download_webpage(t_url, video_id, "get real video_url")
        video_url = re.search(r'file=(http.+?)&', info_cn).group(1)

        info = {
            'id': video_id,
            'title': title,
            'url': video_url,
        }

        return info
