# coding: utf-8

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

class TF1IE(InfoExtractor):
    """
    TF1 uses the wat.tv player, currently it can only download videos with the
    html5 player enabled, it cannot download HD videos or the news.
    """
    _VALID_URL = r'http://videos.tf1.fr/.*-(.*?).html'
    _TEST = {
        u'url': u'http://videos.tf1.fr/auto-moto/citroen-grand-c4-picasso-2013-presentation-officielle-8062060.html',
        u'file': u'6bysb.mp4',
        u'md5': u'66789d3e91278d332f75e1feb7aea327',
        u'info_dict': {
            u"title": u"Citroën Grand C4 Picasso 2013 : présentation officielle"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        id = mobj.group(1)
        webpage = self._download_webpage(url, id)
        embed_url = self._html_search_regex(r'"(https://www.wat.tv/embedframe/.*?)"',
                                webpage, 'embed url')
        embed_page = self._download_webpage(embed_url, id, u'Downloading embed player page')
        wat_id = self._search_regex(r'UVID=(.*?)&', embed_page, 'wat id')
        wat_info = self._download_webpage('http://www.wat.tv/interface/contentv3/%s' % wat_id, id, u'Downloading Wat info')
        wat_info = json.loads(wat_info)['media']
        wat_url = wat_info['url']
        return self.url_result(wat_url, 'Wat')
