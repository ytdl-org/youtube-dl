# coding: utf-8
from __future__ import unicode_literals

import re
from requests_html import HTMLSession

from .common import InfoExtractor

class ThisVidIE(InfoExtractor):
    IE_NAME = 'thisvid'
    IE_DESC = 'thisvid'
    _VALID_URL = r'https?://(?:www\.)?thisvid\.com/videos/(?P<video>\w)'
    
    
    def _real_extract(self, url):

        videoid = ""
        title = ""
        url_video = ""
        height = 0
        width = 0
        filesize = 0
        try:
            session = HTMLSession()
            try:
                r = session.get(url, timeout=60)
                r.html.render(timeout=60)
            except Exception as e:
                print(e)
            session.close()
            video = r.html.find('video', first=True)
            url_video = video.attrs['src']
            if not url_video:
                raise ExtractorError('No url', expected=True)
            title = self._html_search_meta('og:title', r.html.html).rsplit(' - ')[0]
            videoid = self._html_search_meta('og:video:url', r.html.html).rsplit('/')[4]
            self.report_extraction(videoid + " url: " + url)
            height = int(self._html_search_meta('og:video:height', r.html.html))
            width = int(self._html_search_meta('og:video:width', r.html.html))
            filesize = int(session.request("HEAD",url_video).headers['content-length'])

        except Exception as e:
            print(e)

        return {
            'id': videoid,
            'title': title,
            'url': url_video,
            'height': height,
            'width': width,
            'filesize': filesize,
            'ext': 'mp4'
           
        } 



 