# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class FlipagramIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?flipagram\.com/f/(?P<id>[^/?_]+)'
    _TESTS = [{
        'url': 'https://flipagram.com/f/mSxPSOFyid',
        'info_dict': {
            'url': 'https://d2fab04skj7pig.cloudfront.net/4bfd9a5d4733f6a34b2301af3bae0bb402c5a299_967905053_1458804346377.mp4',
            'id': 'mSxPSOFyid',
            'ext': 'mp4',
            'title': 'Video by Irene M Retno Widiati',
        }
    }, {
        'url': 'https://flipagram.com/f/nm44HumIuD',
        'info_dict': {
            'url': 'https://d2fab04skj7pig.cloudfront.net/e6dd15c6b49d7b66306c44790a31f722d46a2322_2128787897_1460930458561.mp4',
            'id': 'nm44HumIuD',
            'ext': 'mp4',
            'title': 'Video by Sarah Willems'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(r'"contentUrl":"(.+?)"', webpage, u'video_URL', fatal=False)

        return{
            'id': video_id,
            'ext': 'mp4',
            'url': video_url,
            'title': self._og_search_title(webpage),
        }
