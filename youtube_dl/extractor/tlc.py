# encoding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from .brightcove import BrightcoveIE


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
            'description': 'Vier Amische und eine Mennonitin wagen in New York'
                '  den Sprung in ein komplett anderes Leben. Begleitet sie auf'
                ' ihrem spannenden Weg.',
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
        iframe = self._download_webpage(iframe_url, title)

        return {
            '_type': 'url',
            'url': BrightcoveIE._extract_brightcove_url(iframe),
            'ie': BrightcoveIE.ie_key(),
        }
