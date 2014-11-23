# encoding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from .brightcove import BrightcoveIE
from .discovery import DiscoveryIE
from ..utils import compat_urlparse


class TlcIE(DiscoveryIE):
    IE_NAME = 'tlc.com'
    _VALID_URL = r'http://www\.tlc\.com\/[a-zA-Z0-9\-]*/[a-zA-Z0-9\-]*/videos/(?P<id>[a-zA-Z0-9\-]*)(.htm)?'

    _TEST = {
        'url': 'http://www.tlc.com/tv-shows/cake-boss/videos/too-big-to-fly.htm',
        'md5': 'c4038f4a9b44d0b5d74caaa64ed2a01a',
        'info_dict': {
            'id': '853232',
            'ext': 'mp4',
            'title': 'Cake Boss: Too Big to Fly',
            'description': 'Buddy has taken on a high flying task.',
            'duration': 119,
        },
    }


class TlcDeIE(InfoExtractor):
    IE_NAME = 'tlc.de'
    _VALID_URL = r'http://www\.tlc\.de/sendungen/[^/]+/videos/(?P<title>[^/?]+)'

    _TEST = {
        'url': 'http://www.tlc.de/sendungen/breaking-amish/videos/#3235167922001',
        'info_dict': {
            'id': '3235167922001',
            'ext': 'mp4',
            'title': 'Breaking Amish: Die Welt da draußen',
            'uploader': 'Discovery Networks - Germany',
            'description': (
                'Vier Amische und eine Mennonitin wagen in New York'
                '  den Sprung in ein komplett anderes Leben. Begleitet sie auf'
                ' ihrem spannenden Weg.'),
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        iframe_url = self._search_regex(
            '<iframe src="(http://www\.tlc\.de/wp-content/.+?)"', webpage,
            'iframe url')
        # Otherwise we don't get the correct 'BrightcoveExperience' element,
        # example: http://www.tlc.de/sendungen/cake-boss/videos/cake-boss-cannoli-drama/
        iframe_url = iframe_url.replace('.htm?', '.php?')
        url_fragment = compat_urlparse.urlparse(url).fragment
        if url_fragment:
            # Since the fragment is not send to the server, we always get the same iframe
            iframe_url = re.sub(r'playlist=(\d+)', 'playlist=%s' % url_fragment, iframe_url)
        iframe = self._download_webpage(iframe_url, title)

        return {
            '_type': 'url',
            'url': BrightcoveIE._extract_brightcove_url(iframe),
            'ie': BrightcoveIE.ie_key(),
        }
