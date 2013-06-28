import json
import re

from .common import InfoExtractor

from ..utils import (
    compat_urllib_parse,
)


class WatIE(InfoExtractor):
    _VALID_URL=r'http://www.wat.tv/.*-(?P<shortID>.*?)_.*?.html'
    IE_NAME = 'wat.tv'
    _TEST = {
        u'url': u'http://www.wat.tv/video/world-war-philadelphia-vost-6bv55_2fjr7_.html',
        u'file': u'6bv55.mp4',
        u'md5': u'0a4fe7870f31eaeabb5e25fd8da8414a',
        u'info_dict': {
            u"title": u"World War Z - Philadelphia VOST"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        short_id = mobj.group('shortID')

        player_data = compat_urllib_parse.urlencode({'shortVideoId': short_id,
                                                     'html5': '1'})
        player_info = self._download_webpage('http://www.wat.tv/player?' + player_data,
                                             short_id, u'Downloading player info')
        player = json.loads(player_info)['player']
        html5_player = self._html_search_regex(r'iframe src="(.*?)"', player,
                                               'html5 player')
        player_webpage = self._download_webpage(html5_player, short_id,
                                                u'Downloading player webpage')

        video_url = self._search_regex(r'urlhtml5 : "(.*?)"', player_webpage,
                                       'video url')
        title = self._search_regex(r'contentTitle : "(.*?)"', player_webpage,
                                   'title')
        thumbnail = self._search_regex(r'previewMedia : "(.*?)"', player_webpage,
                                       'thumbnail')
        return {'id': short_id,
                'url': video_url,
                'ext': 'mp4',
                'title': title,
                'thumbnail': thumbnail,
                }
