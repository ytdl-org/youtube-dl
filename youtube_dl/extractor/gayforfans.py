# coding: utf-8
from __future__ import unicode_literals

import re

from requests_html import HTMLSession

from .common import InfoExtractor

from ..utils import (
    ExtractorError,

)

class GayForFansIE(InfoExtractor):
    IE_NAME = 'gayforfans'
    IE_DESC = 'gayforfans'
    _VALID_URL = r'https://gayforfans\.com/video/(?P<video>[a-zA-Z0-9_-]+)'
    
    
    def _real_init(self):
        pass

    def _real_extract(self, url):

        videoid = ""
        title = ""
        url_video = ""
        height = 0
        width = 0
        filesize = 0
        self.report_extraction(videoid + " url: " + url)
        try:
            session = HTMLSession()
            r = session.get(url, timeout=60)
            #print(r.html.html)
            video_html = r.html.find('video', first=True)
            videoid = video_html.attrs['id']
            width = int(video_html.attrs['width'])
            height = int(video_html.attrs['height'])
            url_video = r.html.find('source', first=True).attrs['src'] 
            if not url_video:
                raise ExtractorError('No url', expected=True)
            title = r.html.find('title', first=True).text
            filesize = int(session.request("HEAD",url_video).headers['content-length'])
            session.close()


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
