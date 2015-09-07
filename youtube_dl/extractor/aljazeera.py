from __future__ import unicode_literals

from .common import InfoExtractor


class AlJazeeraIE(InfoExtractor):
    _VALID_URL = r'http://www\.aljazeera\.com/programmes/.*?/(?P<id>[^/]+)\.html'

    _TEST = {
        'url': 'http://www.aljazeera.com/programmes/the-slum/2014/08/deliverance-201482883754237240.html',
        'info_dict': {
            'id': '3792260579001',
            'ext': 'mp4',
            'title': 'The Slum - Episode 1: Deliverance',
            'description': 'As a birth attendant advocating for family planning, Remy is on the frontline of Tondo\'s battle with overcrowding.',
            'uploader': 'Al Jazeera English',
        },
        'add_ie': ['Brightcove'],
        'skip': 'Not accessible from Travis CI server',
    }

    def _real_extract(self, url):
        program_name = self._match_id(url)
        webpage = self._download_webpage(url, program_name)
        brightcove_id = self._search_regex(
            r'RenderPagesVideo\(\'(.+?)\'', webpage, 'brightcove id')

        return {
            '_type': 'url',
            'url': (
                'brightcove:'
                'playerKey=AQ~~%2CAAAAmtVJIFk~%2CTVGOQ5ZTwJbeMWnq5d_H4MOM57xfzApc'
                '&%40videoPlayer={0}'.format(brightcove_id)
            ),
            'ie_key': 'Brightcove',
        }
