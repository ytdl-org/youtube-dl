# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote
)
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
        'md5': '7fcdb5349354f40d41689bd0fa8db05a',
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
            r'<h4 class="login_register_header"[^>]+>([^<]+)</h4>', webpage, 'title')
        title = title.replace('\n', '')

        video_link_url = self._search_regex(
            r'document\.write\(strencode2\("([^"]+)"\)\);',
            webpage, 'video link')
        video_link_url = compat_urllib_parse_unquote(video_link_url)
        video_link_url = self._search_regex(
            r"src=\'([^\']+)\'", video_link_url, 'video link')

        duration = parse_duration(self._search_regex(
            r'时长:\s*</span>\s*(\d+:\d+)', webpage, 'duration', fatal=False))

        comment_count = int_or_none(self._search_regex(
            r'留言:\s*</span>\s*(\d+)', webpage, 'comment count', fatal=False))

        return {
            'id': video_id,
            'url': video_link_url,
            'ext': 'mp4',
            'title': title,
            'duration': duration,
            'comment_count': comment_count,
            'age_limit': 18
        }