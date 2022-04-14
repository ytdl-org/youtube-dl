# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamggIE(InfoExtractor):
    _VALID_URL = r'https?://(up.)?streamgg\.com/v/(?P<id>\w+)'
    _TEST = {
        "url": 'https://up.streamgg.com/v/r9gb3m95',
        'md5': 'eaf1f163635c868ecbba95d23ba83448',
        'info_dict': {
            'id': '4529aff4',
            'ext': 'mp4',
            'title': 'Goal 2021 13-04-50'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        title = video_id
        video_url = self._html_search_regex(r'<source src="(.+?)"', webpage, 'video URL')
        video_url = video_url.replace("/../", "/")
        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            "title": title
        }
