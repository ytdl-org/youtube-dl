# -*- coding: utf-8 -*-

import re

from .common import InfoExtractor
from ..utils import determine_ext

class SztvHuIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:(?:www\.)?sztv\.hu|www\.tvszombathely\.hu)/([^/]+)/(?P<name>.+)'
    _TEST = {
        u'url': u'http://sztv.hu/hirek/cserkeszek-nepszerusitettek-a-kornyezettudatos-eletmodot-a-savaria-teren-20130909',
        u'file': u'130909zoldnap.mp4',
        u'md5': u'0047eacedc0afd1ceeac99e69173a07e',
        u'info_dict': {
            u"title": u"Cserkészek népszerűsítették a környezettudatos életmódot a Savaria téren",
            u"description" : u'A zöld nap játékos ismeretterjesztő programjait a Magyar Cserkész Szövetség szervezte, akik az ország nyolc városában adják át tudásukat az érdeklődőknek. A PET...',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)
#        file = self._search_regex(r'var fileHtml5 = "...:(.*?)";',
        file = self._search_regex(r'file: "...:(.*?)",',
                                webpage, 'video file')
        title = self._html_search_regex(r'<meta name="title" content="([^"]*)"',
                                webpage, 'video title').rsplit(' - ', 2)[0]
        description = self._html_search_regex(r'<meta name="description" content="([^"]*)"/>',
                                webpage, 'video description')
        thumbnail = self._og_search_thumbnail(webpage)

        video_url = 'http://media.sztv.hu/vod/' + file

        return {'id': name,
                'url' : video_url,
                'title': title,
                'ext': determine_ext(video_url),
                'description': description,
                'thumbnail': thumbnail,
                }
