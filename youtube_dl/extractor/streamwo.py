# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamwoIE(InfoExtractor):
    _VALID_URL = r'https?://streamwo\.com/(?P<id>\w+)'
    _TEST = {
        "url": 'https://streamwo.com/c11cf208',
        'md5': '64a3e444e10f90051725cc1776682b06',
        'info_dict': {
            'id': 'c11cf208',
            'ext': 'mp4',
            'title': 'pexels-rodnae-productions-6192787'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        title = self._html_search_regex(r'<span class="titles">(.+?)</span>', webpage, 'title')
        video_url = self._html_search_regex(r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            "title": title
        }
