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


class SketchySexBaseIE(InfoExtractor):
    _LOGIN_URL = "https://sketchysex.com/sign-in"
    _SITE_URL = "https://sketchysex.com"
    _LOG_OUT = "https://sketchysex.com/sign-out"
    _MULT_URL = "https://sketchysex.com/multiple-sessions"
    _ABORT_URL = "https://sketchysex.com/multiple-sessions/abort"
    _AUTH_URL = "https://sketchysex.com/authorize2"
    _NETRC_MACHINE = 'sketchysex'
    _USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/84.0.4147.135 Safari/537.36"

    def __init__(self):
        self.session = Session()
        self.user_agent = self._USER_AGENT

    def _login(self):
        self.username, self.password = self._get_login_info()
    
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self._set_cookie('sketchysex.com', 'pp-accepted', 'true')
        login_page = self._download_webpage(
            self._SITE_URL,
            None,
            'Downloading site page',
            headers={
                "User-Agent": self.user_agent
            }
        )
        
        cookies = self._get_cookies(self._LOGIN_URL)
        #print(cookies)
        data = {
            "username": self.username,
            "password": self.password,
            "_csrf-token": urllib.parse.unquote(cookies['X-EMA-CSRFToken'].coded_value)
            
        }

        boundary = "-------------------------------" + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999))
        
        out, content = multipart_encode(data, boundary)
        #print(out)
        #print(content)
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Login request',
            data=out,
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                "Content-Type": content,
                "User-Agent": self.user_agent
            }
        )

        
        if self._AUTH_URL in url_handle.geturl():
            data = {
                "email": "a.tgarc@gmail.com",
                "last-name": "Torres",
                "_csrf-token": urllib.parse.unquote(cookies['X-EMA-CSRFToken'].coded_value)
            }
            out, content = multipart_encode(data, "-------------------------------"
                + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999)))
            auth_page, url_handle = self._download_webpage_handle(
                self._AUTH_URL,
                None,
                "Log in ok after auth2",
                data=out,
                headers={
                    "Referer": self._AUTH_URL,
                    "Origin": self._SITE_URL,
                    "Content-Type": content,
                    "User-Agent": self.user_agent
                }
            )

        
        if self._LOGIN_URL in url_handle.geturl():
            error = clean_html(get_element_by_class('login-error', login_page))
            if error:
                raise ExtractorError(
                    'Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

        elif self._MULT_URL in url_handle.geturl():
            abort_page, url_handle = self._download_webpage_handle(
                self._ABORT_URL,
                None,
                "Log in ok after abort sessions",
                headers={
                    "Referer": self._MULT_URL,
                    "User-Agent": self.user_agent
                }
            )
            


    def _log_out(self):
        self._request_webpage(
            self._LOG_OUT,
            None,
            'Log out'
        )

    def _extract_from_page(self, url):
        
        info_dict = []
        
        try:

            content = self.session.request("GET", url).text
            #print(content)
            regex_title = r"<title>(?P<title>.*?)</title>"
            regex_emurl = r"iframe src=\"(?P<embedurl>.*?)\""
            embedurl = ""
            title = ""
            if re.search(regex_title, content):
                title = re.search(regex_title, content).group("title")
            if not title:
                title = "sketchysex"
            if re.search(regex_emurl, content):
                embedurl = re.search(regex_emurl, content).group("embedurl")
            if not embedurl:
                raise ExtractorError("", cause="Can't find any video", expected=True)
            
            self.session.headers['Referer'] = url
            content = self.session.request("GET", embedurl).text

 
            if not self.username in content:
                raise ExtractorError("", cause="It seems you are not logged", expected=True)            
        
            regex_token = r"token: '(?P<tokenid>.*?)'"
            tokenid = ""
            tokenid = re.search(regex_token, content).group("tokenid")
            if not tokenid:
                raise ExtractorError("", cause="Can't find any token", expected=True)
                
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            #print(videourl)

            self.session.headers['Referer'] = embedurl
            
            info = json.loads(self.session.request("GET", videourl).text)

            if not info:
                raise ExtractorError("", cause="Can't find any JSON info", expected=True)

            
            manifesturl = "https://videostreamingsolutions.net/api:ov-embed/manifest/" + info['xdo']['video']['manifest_id'] + "/manifest.m3u8"
            
            formats_m3u8 = self._extract_m3u8_formats(
                manifesturl, None, m3u8_id="hls", fatal=False
            )

            if not formats_m3u8:
                raise ExtractorError("", cause="Can't find any M3U8 format", expected=True)

            self._sort_formats(formats_m3u8)
        
            videoid = str(info['xdo']['video']['id'])
            
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
    _VALID_URL = r"https?://(?:www\.)?sketchysex.com/episode/"
    

    def _real_initialize(self):
        self._login()
        cookies = self._get_cookies(self._LOGIN_URL)
        for key in cookies:
            self.session.cookies.set(key, cookies[key].coded_value)
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": self.user_agent,
        })
        
        #print(self.session.cookies)

    def _real_extract(self, url):
        data = self._extract_from_page(url)
        self._log_out()
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(data['cause'])
        else:
            return(data)


class SketchySexPlayListIE(SketchySexBaseIE):
    IE_NAME = 'sketchysex:playlist'
    IE_DESC = 'sketchysex:playlist'
    _VALID_URL = r"https?://(?:www\.)?sketchysex\.com/episodes/(?P<id>\d+)"
    _BASE_URL = "https://sketchysex.com"


    def _real_initialize(self):
        self._login()
        cookies = self._get_cookies(self._LOGIN_URL)
        for key in cookies:
            self.session.cookies.set(key, cookies[key].coded_value)
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "User-Agent": self.user_agent,

        })

    def _real_extract(self, url):

        playlistid = re.search(self._VALID_URL, url).group("id")

  
        page = self.session.request("GET", url).text
    
        generic_link = re.compile(r'(?<=\")/episode/[^\"]+(?=\")', re.I)

        target_links = list(set(re.findall(generic_link, page)))

    
        entries = []
        for link in target_links:
            
            full_link = self._BASE_URL + link
            self.session.headers['Referer'] = url
            info = self._extract_from_page(full_link)
            if info:
                if not "error" in info['id']:
                    entries.append(info)
            
        self._log_out()
        return self.playlist_result(entries, "sketchysex Episodes:" + playlistid, "sketchysex Episodes:" + playlistid)

