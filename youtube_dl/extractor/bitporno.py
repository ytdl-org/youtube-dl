# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class BitpornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?bitporno\.com/\?v=(?P<id>\w+)'
    _TEST = {
        'url': 'https://www.bitporno.com/?v=FGJWRHQKWB',
        'info_dict': {
            'id': 'FGJWRHQKWB',
            'title': 'SpyFam 2017 06 12 Lana Rhoades XXX 1080p MP4-KTR',
            'ext': 'mp4',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        # There were 1080p videos in Bitporno.com. It seems there've gone.
        # Now there are still 360/480/720p, this extractor only support 720p.
        # 2017.06
        tmp_str = self._html_search_regex(r'"file":"(https:.*?\.mp4)","label":"720p"', webpage, 'file_720p')
        if not tmp_str:
            raise ExtractorError('Note: this Bitporno extractor only support 720p videos.')
        true_url = tmp_str[tmp_str.rfind('https'):].replace("\\", "")
        print('Note: this Bitporno extractor only support 720p videos.\nVideo url: ' + true_url)
        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': true_url,
        }
