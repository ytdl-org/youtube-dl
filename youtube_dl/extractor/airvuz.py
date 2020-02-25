# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class AirVuzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?airvuz\.com/video/(?:.+)?id=(?P<id>.+)'
    _TEST = {
        'url': 'https://www.airvuz.com/video/An-Imaginary-World?id=599e85c49282a717c50f2f7a',
        'info_dict': {
            'id': '599e85c49282a717c50f2f7a',
            'ext': 'mp4',
            'title': 'md5:7fc56270e7a70fa81a5935b72eacbe29',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('og:title', webpage)
        video_url = self._html_search_regex(r'<meta[^>]+?(?:name|property)=(?:\'og:video:url\'|"og:video:url"|og:video:url)[^>]+?content=(?:"([^"]+?)"|\'([^\']+?)\'|([^\s"\'=<>`]+))', webpage, 'video_url')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
