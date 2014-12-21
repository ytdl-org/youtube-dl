from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CBSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cbs\.com/shows/[^/]+/(?:video|artist)/(?P<id>[^/]+)/.*'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '4JUVEwq3wUT7',
            'ext': 'flv',
            'title': 'Connect Chat feat. Garth Brooks',
            'description': 'Connect with country music singer Garth Brooks, as he chats with fans on Wednesday November 27, 2013. Be sure to tune in to Garth Brooks: Live from Las Vegas, Friday November 29, at 9/8c on CBS!',
            'duration': 1495,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }, {
        'url': 'http://www.cbs.com/shows/liveonletterman/artist/221752/st-vincent/',
        'info_dict': {
            'id': 'WWF_5KqY3PK1',
            'ext': 'flv',
            'title': 'Live on Letterman - St. Vincent',
            'description': 'Live On Letterman: St. Vincent in concert from New York\'s Ed Sullivan Theater on Tuesday, July 16, 2014.',
            'duration': 3221,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
        '_skip': 'Blocked outside the US',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        real_id = self._search_regex(
            r"video\.settings\.pid\s*=\s*'([^']+)';",
            webpage, 'real video ID')
        return self.url_result('theplatform:%s' % real_id)
