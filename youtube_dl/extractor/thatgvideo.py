# coding: utf-8
from __future__ import unicode_literals

import re


from .common import InfoExtractor
from ..utils import (
    ExtractorError, 
    std_headers,
    HEADRequest
)



class ThatGVideoIE(InfoExtractor):
    IE_NAME = 'thatgvideo'
    _VALID_URL = r'https?://thatgvideo\.com/videos/(?P<id>\d+).*'

       

    def _real_extract(self, url):

        videoid = self._match_id(url)
        
               
        webpage, urlh = self._download_webpage_handle(url, videoid, "DL webpage")
        
        if 'Video not found' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % videoid, expected=True)

        
        title = None
        mobj = re.search(r"<h1>(?P<title>.+?)<", webpage)
        if mobj:
            title = mobj.group('title').replace(" ","_")
            
        mobj = re.search(r"href=\"(?P<video_url>https://thatgvideo.com/get_file/2/.+?)\"", webpage)
        if mobj:
            video_url = mobj.group('video_url')
            std_headers['Referer'] = url
            std_headers['Accept'] = "*/*"            
            reqhead = HEADRequest(video_url)
            res = self._request_webpage(reqhead, videoid, headers={'Range' : 'bytes=0-'})
            filesize = res.getheader('Content-Lenght', None)
            if filesize:
                filesize = int(filesize)    
            url_video_final = res.headers.get('location', video_url)

            format_video = {
                    'format_id' : "http-mp4",
                    'url' : url_video_final,
                    'filesize' : filesize
                }
            
            entry_video = {
                'id' : videoid,
                'title' : title,
                'formats' : [format_video],
                'ext': "mp4"
            }
                
            return entry_video
                   
        else:
            raise ExtractorError(
                'Video %s does not exist' % videoid, expected=True)

    

              

