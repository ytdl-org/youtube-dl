# coding: utf-8
from __future__ import unicode_literals

import re

from requests import Session

from .common import InfoExtractor
from ..utils import (
    ExtractorError, int_or_none, 
    std_headers,
)

from urllib import parse

import httpx 
import requests

class StreamtapeIE(InfoExtractor):
    IE_NAME = 'streamtape'
    _VALID_URL = r'https?://(?:doodstream|streamtape)\.(?:com|net)/(?:d|e|v)/(?P<id>[a-zA-Z0-9_-]+)(?:(/$)|(/.+?$)|$)'

    @staticmethod
    def _extract_url(webpage):
        
        mobj = re.search(
            r'rel="videolink" href="(?P<real_url>https?://(?:doodstream|streamtape)\.(?:com|net).+?)"', webpage)
        if mobj:
            return mobj.group('real_url')

        mobj = re.search(r"reload_video\('(?P<real_url>https?://(?:doodstream|streamtape)\.(?:com|net).+?)/'", webpage)
        if mobj:
            return mobj.group('real_url')
        



    @staticmethod
    def _extract_info_video(url, video_id):

        client = httpx.Client()
        client.headers['user-agent'] = std_headers['User-Agent']
        res = client.get(url)
        _urlh = res.url #type httpx.URL        
        webpage = res.text
        

        if 'Video not found' in webpage:
            raise ExtractorError(
                'Video %s does not exist' % video_id, expected=True)

       
        #mobj = re.search(r'\("videolink"\)\.innerHTML = "(?P<video_url>.*?)"', webpage)
        title = None
        mobj = re.search(r"<meta name=\"og:title\" content=\"(?P<title>.+?)\">", webpage)
        if mobj:
            title = mobj.group('title').partition(".")[0]
            

        if 'streamtape' in _urlh.netloc:

            mobj = re.search(r"<script>.*?\.innerHTML = (?P<video_url>.*?);</script>", webpage)
            if mobj:
                video_url = mobj.group('video_url')
                url_s = video_url.split("+")
                url_download = "https:"
                for s in url_s:
                    url_download = url_download + s.strip(" \"\'")
                url_download = url_download + "&dl=1"
                res = client.head(url_download,headers=std_headers)
                url_video_final = res.headers.get('location', url_download)
                filesize = int_or_none(res.headers.get('Content-Length'))
                
                format_video = {
                    'format_id' : "http-mp4",
                    'url' : url_video_final,
                    'filesize' : filesize,
                    'ext' : 'mp4'
                }

                return {
                    'id': video_id,
                    'title': title,
                    'formats': [format_video],
                    'ext': 'mp4'
                }

                
        if 'dood.to' or 'doodstream' in _urlh.netloc: 

            mobj = re.search(r"href=\"(?P<video_url>/download/.*?)\"",webpage)
            if mobj:
                video_url = mobj.group('video_url')
            
            cookies = httpx.Cookies()
            cookies.set('dref_url', None, _urlh.netloc)
            res = client.get(f"{_urlh.scheme}://{_urlh.netloc}/e/{video_id}", cookies=cookies)
            webpage = res.text
            mobj = re.search(r"get\('(?P<target_url>/pass_md5.*?)',", webpage)
            if mobj:
                req_url = f"{_urlh.scheme}://{_urlh.netloc}" +  mobj.group('target_url')
                res = client.get(req_url, headers={"accept" : "*/*", "referer" : str(_urlh), "X-Requested-With": "XMLHttpRequest",  })
                url_valid = res.txt


            
                if not video_url.startswith("http"):
                    v_url = f"{_urlh.scheme}://{_urlh.netloc}{video_url}"
                    dl_p = client.get(v_url, headers={"accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", "referer" : str(_urlh)})
                    mobj = re.search(r"window.open\('(?P<vid>.*?)', '_self'\)", dl_p.text)
                    if mobj:
                        url_download = mobj.group('vid')                        
                        res = requests.head(url_download)
                        url_video_final = res.header.get('location', url_download)
                        return({
                            'url': url_video_final,
                            'id': video_id,
                            'title': title,
                            'ext': 'mp4'
                        })
                    

        raise ExtractorError(
            'Video %s does not exist' % video_id, expected=True)




    
    def _real_extract(self, url):
        mobj = re.search(self._VALID_URL, url)
        if mobj:
            video_id = mobj.group('id')
        else:
            raise ExtractorError('Video does not exits')

                
        return self._extract_info_video(url, video_id)
              

