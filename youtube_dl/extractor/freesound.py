# -*- coding: utf-8 -*-
import re

from .common import InfoExtractor

class FreeSoundIE(InfoExtractor):
    _VALID_URL = r'(?:http://)?(?:www\.)?freesound\.org/people/([^/]+)/sounds/([^/]+)'

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