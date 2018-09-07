# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SverigesRadioIE(InfoExtractor):
    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json = self._download_json('https://sverigesradio.se/sida/playerajax/getaudiourl?type=' + self.SR_type + '&quality=high&format=iis&id=' + video_id, video_id)
        audioUrl = json.get('audioUrl')

        # TODO more code goes here, for example ...
        # title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'url': audioUrl,
            'id': video_id,
            'title': self._og_search_title(webpage),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }

class SverigesRadioArtikelIE(SverigesRadioIE):
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/sida/artikel.aspx\?(.*)artikel=(?P<id>[0-9]*)'
    _TEST = {
        'url': 'https://sverigesradio.se/sida/artikel.aspx?programid=83&artikel=7038546',
        'md5': '6a4917e1923fccb080e5a206a5afa542',
        'info_dict': {
            'id': '7038546',
            'ext': 'm4a',
            'title': 'Esa Teittinen: Sanningen har inte kommit fram - Nyheter (Ekot)',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }
    SR_type = 'publication'

class SverigesRadioAvsnittIE(SverigesRadioIE):
    _VALID_URL = r'https?://(?:www\.)?sverigesradio\.se/sida/avsnitt/(?P<id>[0-9]*)'
    _TESTS = [{
        'url': 'https://sverigesradio.se/sida/avsnitt/1140922?programid=1300',
        'md5': '20dc4d8db24228f846be390b0c59a07c',
        'info_dict': {
            'id': '1140922',
            'ext': 'mp3',
            'title': 'Metoo och valen - Konflikt',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }, {
        'url': 'https://sverigesradio.se/sida/avsnitt/1140948?programid=4772',
        'md5': 'b360f34e1931cbd6dbf9c502a4b2e35d',
        'info_dict': {
            'id': '1140948',
            'ext': 'm4a',
            'title': 'Anne Sofie von Otter – efter Benny Fredrikssons död - Söndagsintervjun',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    },
    ]
    SR_type = 'episode'
