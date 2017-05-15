# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote


class XNXXIE(InfoExtractor):
    _VALID_URL = r'https?://(?:video|www)\.xnxx\.com/video-?(?P<id>[0-9a-z]+)/'
    _TESTS = [{
        'url': 'http://www.xnxx.com/video-55awb78/skyrim_test_video',
        'md5': 'ef7ecee5af78f8b03dca2cf31341d3a0',
        'info_dict': {
            'id': '55awb78',
            'ext': 'flv',
            'title': 'Skyrim Test Video',
            'age_limit': 18,
        },
    }, {
        'url': 'http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_',
        'only_matching': True,
    }, {
        'url': 'http://www.xnxx.com/video-55awb78/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._search_regex(r'flv_url=(.*?)&amp;',
                                       webpage, 'video URL')
        video_url = compat_urllib_parse_unquote(video_url)

        video_title = self._html_search_regex(r'<title>(.*?)\s+-\s+XNXX.COM',
                                              webpage, 'title')

        video_thumbnail = self._search_regex(r'url_bigthumb=(.*?)&amp;',
                                             webpage, 'thumbnail', fatal=False)

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'ext': 'flv',
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
