from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    smuggle_url,
)


class CBSIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:cbs\.com/shows/[^/]+/(?:video|artist)|colbertlateshow\.com/(?:video|podcasts))/[^/]+/(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.cbs.com/shows/garth-brooks/video/_u7W953k6la293J7EPTd9oHkSPs6Xn6_/connect-chat-feat-garth-brooks/',
        'info_dict': {
            'id': '4JUVEwq3wUT7',
            'display_id': 'connect-chat-feat-garth-brooks',
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
            'display_id': 'st-vincent',
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
    }, {
        'url': 'http://colbertlateshow.com/video/8GmB0oY0McANFvp2aEffk9jZZZ2YyXxy/the-colbeard/',
        'only_matching': True,
    }, {
        'url': 'http://www.colbertlateshow.com/podcasts/dYSwjqPs_X1tvbV_P2FcPWRa_qT6akTC/in-the-bad-room-with-stephen/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        request = sanitized_Request(url)
        # Android UA is served with higher quality (720p) streams (see
        # https://github.com/rg3/youtube-dl/issues/7490)
        request.add_header('User-Agent', 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5)')
        webpage = self._download_webpage(request, display_id)
        real_id = self._search_regex(
            [r"video\.settings\.pid\s*=\s*'([^']+)';", r"cbsplayer\.pid\s*=\s*'([^']+)';"],
            webpage, 'real video ID')
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/dJ5BDC/%s?mbr=true&manifest=m3u' % real_id,
                {'force_smil_url': True}),
            'display_id': display_id,
        }
