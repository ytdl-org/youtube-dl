# coding: utf-8
from __future__ import unicode_literals

from ..compat import (
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
)
from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
    ExtractorError,
)


class Porn91IE(InfoExtractor):
    IE_NAME = '91porn'
    _VALID_URL = r'(?:https?://)(?:www\.|)91porn\.com/.+?\?viewkey=(?P<id>[\w\d]+)'

    _TEST = {
        'url': 'http://91porn.com/view_video.php?viewkey=7e42283b4f5ab36da134',
        'md5': '6df8f6d028bc8b14f5dbd73af742fb20',
        'info_dict': {
            'id': '7e42283b4f5ab36da134',
            'title': '18岁大一漂亮学妹，水嫩性感，再爽一次！',
            'ext': 'mp4',
            'duration': 431,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._set_cookie('91porn.com', 'language', 'cn_CN')

        webpage = self._download_webpage(
            'http://91porn.com/view_video.php?viewkey=%s' % video_id, video_id)

        if '作为游客，你每天只可观看10个视频' in webpage:
            raise ExtractorError('91 Porn says: Daily limit 10 videos exceeded', expected=True)

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
        url_params = compat_urllib_parse_urlencode({
            'VID': file_id,
            'mp4': '1',
            'seccode': sec_code,
            'max_vid': max_vid,
        })
        info_cn = self._download_webpage(
            'http://91porn.com/getfile.php?' + url_params, video_id,
            'Downloading real video url')
        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'file=([^&]+)&', info_cn, 'url'))

        duration = parse_duration(self._search_regex(
            r'时长:\s*</span>\s*(\d+:\d+)', webpage, 'duration', fatal=False))

        comment_count = int_or_none(self._search_regex(
            r'留言:\s*</span>\s*(\d+)', webpage, 'comment count', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'duration': duration,
            'comment_count': comment_count,
            'age_limit': self._rta_search(webpage),
        }
