# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VimpOTHRVideoIE(InfoExtractor):
    _VALID_URL = r'https?://vimp\.oth-regensburg\.de/video/(?P<title>[a-zA-Z0-9_-]+)/(?P<id>[a-z0-9]{32})'
    _TEST = {
        'url': 'https://vimp.oth-regensburg.de/video/VE2-Vorlesungsaufzeichnung-von-Fr-5November/ca47954b51baa0f0fb1481cc4df0558a',
        'md5': 'eabb43c7bcc884773b0b0d2e37ebae87',
        'info_dict': {
            'id': 'ca47954b51baa0f0fb1481cc4df0558a',
            'ext': 'mp4',
            'title': 'VE2-Vorlesungsaufzeichnung von Fr. 5.November',
            'description': 'Invarianzsatz, Rentenbarwerte',
            'thumbnail': 'https://vimp.oth-regensburg.de/cache/b56c79d598c594b117d769dc1731ed6a.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title') or self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'title': title,
            'url': self._og_search_video_url(webpage),
            'thumbnail': thumbnail,
            'description': description,
        }
