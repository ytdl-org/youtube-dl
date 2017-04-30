# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    int_or_none
)


class Zaq1IE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?zaq1\.pl/video/(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://zaq1.pl/video/xev0e',
        'md5': '24a5eb3f052e604ae597c4d0d19b351e',
        'info_dict': {
            'id': 'xev0e',
            'title': 'DJ NA WESELE. TANIEC Z FIGURAMI.węgrów/sokołów podlaski/siedlce/mińsk mazowiecki/warszawa',
            'ext': 'mp4',
            'duration': 511,
            'uploader': 'Anonim',
            'upload_date': '20170330',
        }
    }, {
        'url': 'http://zaq1.pl/video/x80nc',
        'md5': '1245973520adc78139928a820959d9c5',
        'info_dict': {
            'id': 'x80nc',
            'title': 'DIY Inspiration Challenge #86 | koraliki | gwiazdka na choinkę z koralików i drutu',
            'ext': 'mp4',
            'duration': 438,
            'uploader': 'Anonim',
            'upload_date': '20170404',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'(?s)<h1>\s*<span.+class="watch-title".+title="([^"]+)">\1\s*</span>\s*</h1>', webpage, 'title')

        div = self._search_regex(r'(?s)(?P<div><div.+id=(["\'])video_player\2.+</div>)', webpage, 'video url', group='div')
        video_url = self._search_regex(r'data-video-url="(http[^"]+)"', div, 'video url')

        ext = self._search_regex(r'data-file-extension="([^"]+)"', div, 'ext', None, False)
        duration = int_or_none(self._search_regex(r'data-duration="([^"]+)"', div, 'duration', None, False))
        thumbnail = self._search_regex(r'data-photo-url="([^"]+)"', div, 'thumbnail', None, False)

        upload_date = unified_strdate(self._search_regex(r'<strong\s+class="watch-time-text">\s*Opublikowany\s+([0-9]{4}-[0-9]{2}-[0-9]{2})', webpage, 'upload date'))
        uploader = self._search_regex(r'<div\s+id="watch7-user-header">.*Wideo dodał:\s*<a[^>]*>\s*([^<]+)\s*</a>', webpage, 'uploader')

        return {
            'id': video_id,
            'title': title,
            'formats': [{
                'url': video_url,
                'ext': ext,
                'http_headers': {'Referer': url},
            }],
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
            'duration': duration,
        }
