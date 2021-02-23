# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamwoIE(InfoExtractor):
    _VALID_URL = r'https?://streamwo\.com/(?P<id>\w+)'
    _TEST = {
        "url": 'https://streamwo.com/c11cf208',
        'md5': '64a3e444e10f90051725cc1776682b06',
        'info_dict': {
            'id': 'zrxKAY8',
            'ext': 'mp4',
            'title': "Imgur"
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        self.report_extraction(video_id)
        video_url = self._html_search_regex(r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
        if video_url:
            return self.url_result(video_url, ie="Generic")
        return self.url_result(url, ie='Generic')
