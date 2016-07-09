# coding: utf-8
from __future__ import unicode_literals

from .mtv import MTVServicesInfoExtractor
from ..compat import compat_urllib_parse_urlencode


class NextMovieIE(MTVServicesInfoExtractor):
    IE_NAME = 'nextmovie.com'
    _VALID_URL = r'https?://(?:www\.)?nextmovie\.com/shows/[^/]+/\d{4}-\d{2}-\d{2}/(?P<id>[^/?#]+)'
    _FEED_URL = 'http://lite.dextr.mtvi.com/service1/dispatch.htm'
    _TESTS = [{
        'url': 'http://www.nextmovie.com/shows/exclusives/2013-03-10/mgid:uma:videolist:nextmovie.com:1715019/',
        'md5': '09a9199f2f11f10107d04fcb153218aa',
        'info_dict': {
            'id': '961726',
            'ext': 'mp4',
            'title': 'The Muppets\' Gravity',
        },
    }]

    def _get_feed_query(self, uri):
        return compat_urllib_parse_urlencode({
            'feed': '1505',
            'mgid': uri,
        })

    def _real_extract(self, url):
        mgid = self._match_id(url)
        return self._get_videos_info(mgid)
