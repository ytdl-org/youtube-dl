# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError, 
    HEADRequest,
    std_headers
)




class CumlouderIE(InfoExtractor):
    IE_NAME = 'cumlouder'
    _VALID_URL = r'https?://(www\.)?cumlouder\.com'


    
    def _real_extract(self, url):

               
        webpage, _ = self._download_webpage_handle(url,None, "Downloading video webpage")
        title = None
        mobj = re.search(r"<title>(?P<title>.+?)</title>", webpage)
        title = ""
        if mobj:
            title = mobj.group('title')
            title = title.partition(" | ")[0]
            title = title.replace(" ", "_").replace(",","")

        if not title:
            title = url.rsplit("/")[0].replace("-","_")
        video_url = ""
        height = None
        weight = None
        mobj = re.search(r'<source src="(?P<video_url>.*)" type=\'video/mp4\' label=\'(?P<w>.*)p\' res=\'(?P<h>.*)\'', webpage)
        if mobj:
            video_url = mobj.group('video_url')
            video_url = video_url.replace("&amp;", "&")
            weight = int(mobj.group('w'))
            height = int(mobj.group('h'))
        if not video_url:
            raise ExtractorError("video not found")
        video_id = ""
        mobj = re.search(r'track_video.php\?s=(?P<video_id>.*)"', webpage)
        if mobj:
            video_id = mobj.group('video_id')
        if not video_id:
            video_id = 'cumlouder'

        
        std_headers['Referer'] = url
        std_headers['Accept'] = "*/*"
        reqhead = HEADRequest(video_url)
        res = self._request_webpage(reqhead, None, headers={'Range' : 'bytes=0-'})
        filesize = res.getheader('Content-Lenght')
        if filesize:
            filesize = int(filesize)

        format_video = {
            'format_id' : 'http-mp4',
            'url' : video_url,
            'filesize' : filesize,
            'weight' : weight,
            'height' : height
        }
        


        entry_video = {
            'id' : video_id,
            'title' : title,
            'formats' : [format_video],
            'ext' : 'mp4'
        }
                        
        return entry_video
              

