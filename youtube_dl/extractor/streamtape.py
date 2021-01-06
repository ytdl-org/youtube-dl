# coding: utf-8
from __future__ import unicode_literals

import re

from requests import Session

from .common import InfoExtractor
from ..utils import (
    ExtractorError, 
    std_headers   
)

import requests

class StreamtapeIE(InfoExtractor):
    IE_NAME = 'streamtape'
    _VALID_URL = r'https?://streamtape\.com/(?:e|v)/(?P<id>[a-zA-Z0-9_-]+)(?:(/$)|(/.+?$)|$)'

    @staticmethod
    def _extract_url(webpage):
        
        mobj = re.search(
            r'rel="videolink" href="(?P<real_url>https://streamtape\.com.+?)"', webpage)
        if mobj:
            return mobj.group('real_url')

        mobj = re.search(r"reload_video\('(?P<real_url>https://streamtape\.com.+?)/'", webpage)
        if mobj:
            return mobj.group('real_url')
        



    @staticmethod
    def _extract_info_video(webpage, video_id):
        if 'Video not found' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        print(webpage)
        mobj = re.search(r'\("videolink"\)\.innerHTML = "(?P<video_url>.*?)"', webpage)
        if mobj:
            video_url = mobj.group('video_url')

        else:
            raise ExtractorError(
            'Video %s does not exist' % video_id, expected=True)

        title = None
        mobj = re.match(r'<meta name="og:title" content="(?P<title>.+?)">', webpage)
        if mobj:
            title = mobj.group('title')
        
        if not title:
            title = 'streamtape'


        #resp = requests.head('https:' + video_url + '&stream=1')
        #url_download = resp.headers.get('Location')
        url_download = 'https:' + video_url + '&dl=1'
        print(url_download) 

        headers = std_headers

        print(headers)
       
        # headers = {
        #     "acccept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        #     "pragma": "no-cache",
        #     "cache-control": "no-cache",
        #     #"sec-fetch-site": "none",
        #     #"sec-fetch-mode": "navigate",
        #     #"sec-fetch-dest": "document",
        #     "accept-language": "es-ES,es;q=0.9,en;q=0.8,gl;q=0.7,ja;q=0.6",

        # }   
        # session.headers.update(headers)
        # print(session.headers)    
        res = requests.head(url_download,headers=headers)
        print(res.headers)
        url_video = res.headers['location']
        print(url_video)
        
               
        return ({
            'url': url_video,
            'id': video_id,
            'title': title,
            'ext': 'mp4'
        })



    
    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)
        if mobj:
            video_id = mobj.group('id')
        else:
            raise ExtractorError('Video does not exits')

        webpage = self._download_webpage(url, video_id)
        if 'Video not found' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)
        
        return self._extract_info_video(webpage, video_id)
              

