# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    int_or_none
)


class GayForITEUIE(InfoExtractor):
    
    _VALID_URL = r'https?://(?:www\.)gayforit\.eu/(?:playvideo.php\?vkey\=(?P<vkey>[\w-]+)|video/(?P<id>\d+))'

    def _real_extract(self, url):
        
        videoid = self._search_regex(self._VALID_URL, url, 'videoid',default=None, fatal=False, group='id' )

        webpage = self._download_webpage(url, videoid, "Downloading video webpage")

        title = self._search_regex(r'<title>GayForIt - Free Gay Porn Videos - ([\w\s]+)</title>', webpage, 'title', default=None, fatal=False)
        
        if title: title=title.replace(" ","_")
        else: title="GayForIt_eu"
        
        video_url = self._search_regex(r'<source src=\"([^\"]+)\" type=\"video/mp4', webpage, 'videourl', default=None, fatal=False)

        if not video_url:
            raise ExtractorError("no video url")
        
        if not videoid:
            videoid = self._search_regex(r'content/(\d+)/mp4', video_url, 'videoid', default="no_id")
  


        res = self._request_webpage(HEADRequest(video_url), videoid, headers={'Referer' : url, 'Range' : 'bytes=0-'})

        filesize =  int_or_none(res.headers.get('Content-Length'))
        
        format_video = {
            'format_id' : "http-mp4",
            'url' : video_url,
            'filesize' : filesize,
            'ext' : 'mp4'
         }

        return {
            'id': videoid,
            'title': title,
            'formats': [format_video],
            'ext': 'mp4'
        }
