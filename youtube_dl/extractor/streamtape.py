# coding: utf-8
from __future__ import unicode_literals

import re

from requests.sessions import session

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

    @staticmethod
    def _extract_info_video(url):
        mobj = re.match(StreamtapeIE._VALID_URL, url)
        if mobj:
            video_id = mobj.group('id')
        else:
            raise ExtractorError('Video does not exits')

        headers = std_headers

        session = requests.Session(headers=headers)
        webpage = session.get(url).text

        if 'Video not found' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

        mobj = re.search(
            r'<div id="videolink" style="display:none;">(?P<video_url>[^<]+)</div>', webpage)
        if mobj:
            video_url = mobj.group('video_url')

        else:
            raise ExtractorError(
            'Video %s does not exist' % video_id, expected=True)

        mobj = re.match(r'<meta name="og:title" content="(?P<title>.+?)">', webpage)
        title = None
        if mobj:
            title = mobj.group('title')

        #resp = requests.head('https:' + video_url + '&stream=1')
        #url_download = resp.headers.get('Location')
        url_download = 'https:' + video_url + '&stream=1'
        
               
        return ({
            'url': url_download,
            'id': video_id,
            'title': title,
            'ext': 'mp4',
            'http_headers': {'Referer': url, 'Origin':'https://streamtape.com', 'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5', 'Accept-Language': 'es-ES,en-US;q=0.7,en;q=0.3', 'Range': 'bytes=0-', 'Accept-Encoding': 'gzip, deflate, br'}
        })



    
    def _real_extract(self, url):
        return self._extract_info_video(url)
              

