# coding: utf-8
from __future__ import unicode_literals

import json
import re
import random
import urllib.parse
from requests import Session

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    ExtractorError,
    clean_html,
    get_element_by_class)


class TimFuckBaseIE(InfoExtractor):
    _LOGIN_URL = "https://treasureislandmedia.com/members/login"
    _LOGOUT_URL = "https://treasureislandmedia.com/members/logout"
    _SITE_URL = "https://treasureislandmedia.com"
    _NETRC_MACHINE = 'timfuck'
    
    
    def _login(self):
        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        
        login_page = self._download_webpage(
            self._LOGIN_URL,
            None,
            'Downloading login page',
        )
        login_attempt_id = self._hidden_inputs(login_page)['login_attempt_id']
                
        data = {
            "amember_login": username,
            "amember_pass": password,
            "login_attemp_id": login_attempt_id,
            "amember_redirect_url": self._SITE_URL            
        }

        boundary = "-------------------------------" + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999))
        
        out, content = multipart_encode(data, boundary)
        res = self._download_webpage(
            self._LOGIN_URL,
            None,
            'Login request',
            data=out,
            headers={
                "Referer": "https://treasureislandmedia.com/members/login?amember_redirect_url=https//treasureislandmedia.com/",
                "Origin": self._SITE_URL,
                "Content-Type": content,
            }
        )

        if "error" in res:        
            raise ExtractorError('Unable to log in', True)

        
           


    def _log_out(self):
        self._request_webpage(
            self._LOGOUT_URL,
            None,
            'Log out'
        )

    def _extract_from_page(self, url):
        
        
        try:

            content = self._download_webpage(
                url,
                None,
                'Video webpage'
            )
            videoid = self._search_regex(
            r"\"#timfpvid-(?P<videoid>.*?)\"", content, 'videoid', default=None)
            regex_title = r"<title>(?P<title>.*?)</title>"       
            regex_emurl = r"type: \"application/x-mpegurl\",  src: \"(?P<embedurl>.*?)\""
            regex_emurl2 = r"type: \"video/mp4\",  src: \"(?P<embedurl>.*?)\""
            embedurl_mp4 = ""
            embedurl_hls = ""
            title = ""
            if re.search(regex_title, content):
                title = re.search(regex_title, content).group("title")        
            if not title:
                title = "timfuck"
            if re.search(regex_emurl, content):
                embedurl_hls = re.search(regex_emurl, content).group("embedurl")  
            if re.search(regex_emurl2, content):
                embedurl_mp4 = re.search(regex_emurl2, content).group("embedurl")           
            if not embedurl_mp4 and not embedurl_hls:
                raise ExtractorError("", cause="Can't find any video", expected=True)
            
                        
            if embedurl_hls:
                
                formats_m3u8 = self._extract_m3u8_formats(
                embedurl_hls, videoid, m3u8_id="hls", ext="mp4", fatal=False
                )

                if not formats_m3u8:
                    raise ExtractorError("", cause="Can't find any M3U8 format", expected=True)

                self._sort_formats(formats_m3u8)

                info = {
                    "id": videoid,
                    "title": title,
                    "formats": formats_m3u8,
                    "ext": "mp4",
                
                }
            
            if embedurl_mp4:

                info = {
                    "_type": "url",
                    "id": videoid,
                    "title": title,
                    "url" : embedurl_mp4,
                    "ext": "mp4",
                
                }   
          
            return info
        
        except ExtractorError as e:
            return({
                "id" : "error",
                "cause" : e.cause
            })



class TimFuckIE(TimFuckBaseIE):
    IE_NAME = 'timfuck'
    IE_DESC = 'timfuck'
    _VALID_URL = r"https?://(?:www\.)?(?P<host>.*?)treasureislandmedia.com/scenes/\w"
    

    def _real_initialize(self):
        self._login()


    def _real_extract(self, url):
        data = self._extract_from_page(url)
      
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(data['cause'])
        else:
            return(data)


