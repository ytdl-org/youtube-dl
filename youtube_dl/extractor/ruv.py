# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class RuvIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ruv\.is/sarpurinn/ruv/\w+/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://ruv.is/sarpurinn/ruv/frettir/20170614',
        'md5': 'a07ea1ebaba64082d90323b1c96f264b',
        'info_dict': {
            'id': '20170614',
            'ext': 'mp4',
            'title': 'Fréttir',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        video_url = self._html_search_regex(r'video\.src\s*=\s*["\'](.+?)["\']', webpage, 'video URL')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4'
        }
