from __future__ import unicode_literals

import re

from .common import InfoExtractor


class HowcastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?howcast\.com/videos/(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.howcast.com/videos/390161-How-to-Tie-a-Square-Knot-Properly',
        'md5': '8b743df908c42f60cf6496586c7f12c3',
        'info_dict': {
            'id': '390161',
            'ext': 'mp4',
            'description': 'The square knot, also known as the reef knot, is one of the oldest, most basic knots to tie, and can be used in many different ways. Here\'s the proper way to tie a square knot.', 
            'title': 'How to Tie a Square Knot Properly',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_url = self._search_regex(r'\'?file\'?: "(http://mobile-media\.howcast\.com/[0-9]+\.mp4)',
            webpage, 'video URL')

        video_description = self._html_search_regex(r'<meta content=(?:"([^"]+)"|\'([^\']+)\') name=\'description\'',
            webpage, 'description', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': self._og_search_title(webpage),
            'description': video_description,
            'thumbnail': self._og_search_thumbnail(webpage),
        }
