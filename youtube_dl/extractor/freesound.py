# -*- coding: utf-8 -*-
import re

from .common import InfoExtractor

class FreeSoundIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?freesound\.org/people/([^/]+)/sounds/([^/]+)'
    _TEST = {
        u'url': u'http://www.freesound.org/people/miklovan/sounds/194503/',
        u'file': u'194503.mp3',
        u'md5': u'12280ceb42c81f19a515c745eae07650',
        u'info_dict': {
            u"title": u"gulls in the city.wav by miklovan",
            u"uploader" : u"miklovan"
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        music_id = mobj.group(2)
        webpage = self._download_webpage(url, music_id)
        title = self._html_search_regex(r'<meta property="og:title" content="([^"]*)"',
                                webpage, 'music title')
        music_url = self._html_search_regex(r'<meta property="og:audio" content="([^"]*)"',
                                webpage, 'music url')       
        uploader = self._html_search_regex(r'<meta property="og:audio:artist" content="([^"]*)"',
                                webpage, 'music uploader')                                                                        
        ext = music_url.split('.')[-1]

        return [{
            'id':       music_id,
            'title':    title,            
            'url':      music_url,
            'uploader': uploader,
            'ext':      ext,
        }]