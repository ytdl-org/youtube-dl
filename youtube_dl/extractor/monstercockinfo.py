# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    int_or_none,
    sanitize_filename
)


class MonsterCockInfoIE(InfoExtractor):
    
    _VALID_URL = r'https?://(?:www\.)monstercock\.info/video/.*-(?P<id>\d+)\.html'

    def _real_extract(self, url):
        
        videoid = self._search_regex(self._VALID_URL, url, 'videoid',default=None, fatal=False, group='id')

        webpage = self._download_webpage(url, videoid, "Downloading video webpage")

        title = self._search_regex(r'<title>([^<]+)</title>', webpage, 'title', default=None, fatal=False)
        
        title = title.replace("- Videos - monstercock.info", "")
        
         
        video_url = self._search_regex(r'<source src=\"([^\"]+)\"', webpage, 'videourl', default=None, fatal=False)

        if not video_url:
            raise ExtractorError("no video url")        
  


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
            'title': sanitize_filename(title,restricted=True),
            'formats': [format_video],
            'ext': 'mp4'
        }
