# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote


class MalemotionIE(InfoExtractor):
    _VALID_URL = r'https?://malemotion\.com/video/(.+?)\.(?P<id>.+?)(#|$)'
    _TEST = {
        'url': 'http://malemotion.com/video/bete-de-concours.ltc',
        'md5': '3013e53a0afbde2878bc39998c33e8a5',
        'info_dict': {
            'id': 'ltc',
            'ext': 'mp4',
            'title': 'Bête de Concours',
            'age_limit': 18,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'<source type="video/mp4" src="(.+?)"', webpage, 'video URL'))
        video_title = self._html_search_regex(
            r'<title>(.*?)</title', webpage, 'title')
        video_thumbnail = self._search_regex(
            r'<video .+?poster="(.+?)"', webpage, 'thumbnail', fatal=False)

        formats = [{
            'url': video_url,
            'ext': 'mp4',
            'format_id': 'mp4',
            'preference': 1,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
