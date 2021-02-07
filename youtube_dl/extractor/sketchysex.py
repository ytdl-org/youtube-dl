# coding: utf-8
from __future__ import unicode_literals

import json
import re
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    HEADRequest, multipart_encode,
    ExtractorError,
    clean_html,
    get_element_by_class,
    std_headers
)

import logging

class SketchySexBaseIE(InfoExtractor):
    _LOGIN_URL = "https://sketchysex.com/sign-in"
    _SITE_URL = "https://sketchysex.com"
    _LOG_OUT = "https://sketchysex.com/sign-out"
    _MULT_URL = "https://sketchysex.com/multiple-sessions"
    _ABORT_URL = "https://sketchysex.com/multiple-sessions/abort"
    _AUTH_URL = "https://sketchysex.com/authorize2"
    _NETRC_MACHINE = 'sketchysex'



    def __init__(self):

        self.headers = dict()
 
    def initcfg(self):
        self.islogged()
        self._abort()
        self._login()
        data = dict()
        data['headers'] = self.headers
        data['cookies'] = self._get_cookies(self._URL_COOKIES)
        return data

    def islogged(self):

        webpage, _ = self._download_webpage_handle(
            self._SITE_URL,
            None,
            headers=self.headers
        )

        return ("Log Out" in webpage)
    
    def _abort(self):

        self.headers.update({
            "Referer": self._MULT_URL,
        })
        abort_page, url_handle = self._download_webpage_handle(
            self._ABORT_URL,
            None,
            "Log in ok after abort sessions",
            headers=self.headers
        )


    def _login(self):
        self.username, self.password = self._get_login_info()

        self.report_login()
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self._set_cookie('sketchysex.com', 'pp-accepted', 'true')

        self._download_webpage_handle(
            self._SITE_URL,
            None,
            'Downloading site page',
            headers=self.headers
        )
        self.headers.update({"Referer" : "https://sketchysex.com/episodes/1"})
        self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            headers=self.headers
        )
        self.cookies = self._get_cookies(self._LOGIN_URL)
        #print(cookies)
        data = {
            "username": self.username,
            "password": self.password,
            "submit1" : "Log In",
            "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
            
        }

        boundary = "-----------------------------" + str(random.randrange(11111111111111111111111111111, 99999999999999999999999999999))
        
        
        out, content = multipart_encode(data, boundary)        
        #print(out)
        #print(content)
        self.headers.update({
            "Referer": self._LOGIN_URL,
            "Origin": self._SITE_URL,
            "Content-Type": content,            
        })
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Login request',
            data=out,
            headers=self.headers
        )

        del self.headers["Content-Type"]
        del self.headers["Origin"]
        if self._AUTH_URL in url_handle.geturl():
            data = {
                "email": "a.tgarc@gmail.com",
                "last-name": "Torres",
                "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
            }
            out, content = multipart_encode(data, boundary)
            self.headers.update({
                "Referer": self._AUTH_URL,
                "Origin": self._SITE_URL,
                "Content-Type": content,               
            })
            auth_page, url_handle = self._download_webpage_handle(
                self._AUTH_URL,
                None,
                "Log in ok after auth2",
                data=out,
                headers=self.headers
            )
            del self.headers["Content-Type"]
            del self.headers["Origin"]

        
        if self._LOGIN_URL in url_handle.geturl():
            error = clean_html(get_element_by_class('login-error', login_page))
            if error:
                raise ExtractorError(
                    'Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

        elif self._MULT_URL in url_handle.geturl():

            self._abort()



    def _log_out(self):
        self._request_webpage(
            self._LOG_OUT,
            None,
           'Log out'
       )

    def _extract_from_page(self, url):
        
        info_dict = []
        
        try:

            content, _ = self._download_webpage_handle(url, None, "Downloading video web page", headers=self.headers)
            #print(content)
            regex_title = r"<title>(?P<title>.*?)</title>"
            regex_emurl = r"iframe src=\"(?P<embedurl>.*?)\""
            embedurl = ""
            title = ""
            if re.search(regex_title, content):
                title = re.search(regex_title, content).group("title")
            if not title:
                title = url.rsplit("/", 1)[1].replace("-","_")
            else:
                title = title.split(" :: ")[0].replace(" ", "_")
                title = title.replace("/","_")
            if re.search(regex_emurl, content):
                embedurl = re.search(regex_emurl, content).group("embedurl")
            if not embedurl:
                raise ExtractorError("", cause="Can't find any video", expected=True)
            
            self.headers.update({'Referer' : url})
            content, _ = self._download_webpage_handle(embedurl, None, "Downloading embed video", headers=self.headers)
            #content = (webpage.read()).decode('utf-8')
            
            #print(content)
            if not self.username in content:
                raise ExtractorError("", cause="It seems you are not logged", expected=True)            
        
            regex_token = r"token: '(?P<tokenid>.*?)'"
            tokenid = ""
            tokenid = re.search(regex_token, content).group("tokenid")
            if not tokenid:
                raise ExtractorError("", cause="Can't find any token", expected=True)
                
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            #print(videourl)

            self.headers.update({
                "Referer" : embedurl,
                "Accept" : "*/*",
                "X-Requested-With" : "XMLHttpRequest"})
            info = self._download_json(videourl, None, headers=self.headers)

            if not info:
                raise ExtractorError("", cause="Can't find any JSON info", expected=True)

            #print(info)
            videoid = str(info['xdo']['video']['id'])
            manifesturl = "https://videostreamingsolutions.net/api:ov-embed/manifest/" + info['xdo']['video']['manifest_id'] + "/manifest.m3u8"
            
            formats_m3u8 = self._extract_m3u8_formats(
                manifesturl, videoid, m3u8_id="hls", ext="mp4", entry_protocol='m3u8_native', fatal=False
            )

            if not formats_m3u8:
                raise ExtractorError("", cause="Can't find any M3U8 format", expected=True)

            self._sort_formats(formats_m3u8)
        
                        
            info_dict = {
                "id":str(info['xdo']['video']['id']),
                "title": title,
                "formats": formats_m3u8

            }
          
            return info_dict
        
        except ExtractorError as e:
            return({
                "id" : "error",
                "cause" : e.cause
            })



class SketchySexIE(SketchySexBaseIE):
    IE_NAME = 'sketchysex'
    IE_DESC = 'sketchysex'
    _VALID_URL = r'https?://(?:www\.)?sketchysex.com/episode/.*'
    _URL_COOKIES = "https://sketchysex.com"
    
    def _real_initialize(self):

        if not self.islogged():
            self._login()
        self.headers.update({            
            "Referer" : "https://sketchysex.com/episodes/1",
        })
        self.username, self.password = self._get_login_info() 

    def _real_extract(self, url):
        data = self._extract_from_page(url)
        #self._log_out()
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(str(data['cause']))
        else:
            return(data)

class SketchySexPlayListIE(SketchySexBaseIE):
    IE_NAME = 'sketchysex:playlist'
    IE_DESC = 'sketchysex:playlist'
    _VALID_URL = r"https?://(?:www\.)?sketchysex\.com/episodes/(?P<id>\d+)"
    _BASE_URL = "https://sketchysex.com"
    _BASE_URL_PL = "https://sketchysex.com/episodes/"

    def _real_initialize(self):
        if not self.islogged():
            self._login()          
        self.headers.update({
            "Referer" : self._LOGIN_URL,
        })
        self.username, self.password = self._get_login_info() 

    def _real_extract(self, url):

        playlistid = re.search(self._VALID_URL, url).group("id")

        entries = []

        i = 0

        while True:

            url_pl = f"{self._BASE_URL_PL}{int(playlistid) + i}"

            print(url_pl)
        
            content, _ = self._download_webpage_handle(url_pl, None, headers=self.headers)
        
            episodes = re.findall(r'<h1><a href=\"(/episode/.*?)\">(.*?)<', content)
           
    
            for ep in episodes:
                
                entries.append(self.url_result(self._BASE_URL + ep[0], ie=SketchySexIE.ie_key(), video_title=ep[1].replace(" ","_").replace("/","_")))

            if "NEXT>" in content:
                i += 1
            else:
                break
            
            
        self._log_out()
        return self.playlist_result(entries, f"sketchysex Episodes:{playlistid}", f"sketchysex Episodes:{playlistid}")


        

