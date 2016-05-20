# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor


class FavourMeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:favour\.me|likeafool\.com)/video/(?P<id>\d{5})/(?P<display_id>[^/?]+)'
    _TESTS = [{
        'url': 'http://www.favour.me/video/13814/this-mom039s-experiment-proves-that-bottled-water-is-not-as-quothealthyquot-as-it-claims',
        'md5': '44f1421a365637a6c3d4f0c2f5b60df8',
        'info_dict': {
            'id': '13814',
            'title': 'This Mom\'s Experiment Proves That Bottled Water Is Not As "Healthy" As It Claims',
            'ext': 'mp4',
            'uploader': 'www.favour.me',
        }
    }, {
        'url': 'http://www.likeafool.com/video/13799/moose-unexpectedly-gives-birth-to-twins',
        'md5': '5b775f8d51dcc227e9a25a9448bfb2d1',
        'info_dict': {
            'id': '13799',
            'title': 'Moose Unexpectedly Gives Birth To Twins',
            'ext': 'mp4',
            'uploader': 'www.likeafool.com',
        }
    }]

    def _real_extract(self, url):
        video_id, display_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, display_id)
        iframe_url = self._search_regex(r'<iframe[^>]+src="([^">]+)"', webpage, 'iframe URL')

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'display_id': display_id,
            'url': iframe_url,
            'title': self._html_search_regex(r'<title>(.+)\s+\|.+</title>', webpage, 'title'),
        }
