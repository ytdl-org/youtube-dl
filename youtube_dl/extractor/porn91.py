# encoding: utf-8
from __future__ import unicode_literals

from ..compat import compat_urllib_parse
from .common import InfoExtractor


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
        video_id = self._match_id(url)
        url = 'http://91porn.com/view_video.php?viewkey=%s' % video_id
        self._set_cookie('91porn.com', 'language', 'cn_CN')
        webpage = self._download_webpage(url, video_id, "get HTML content")
        title = self._search_regex(
            r'<div id="viewvideo-title">([^<]+)</div>', webpage, 'title')
        title = title.replace('\n', '')

        # get real url
        file_id = self._search_regex(
            r'so.addVariable\(\'file\',\'(\d+)\'', webpage, 'file id')
        sec_code = self._search_regex(
            r'so.addVariable\(\'seccode\',\'([^\']+)\'', webpage, 'sec code')
        max_vid = self._search_regex(
            r'so.addVariable\(\'max_vid\',\'(\d+)\'', webpage, 'max vid')
        url_params = compat_urllib_parse.urlencode({
            'VID': file_id,
            'mp4': '1',
            'seccode': sec_code,
            'max_vid': max_vid,
        })
        info_cn = self._download_webpage(
            'http://91porn.com/getfile.php?' + url_params, video_id,
            "get real video url")
        video_url = self._search_regex(r'file=([^&]+)&', info_cn, 'url')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
