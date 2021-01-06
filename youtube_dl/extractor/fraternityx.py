# coding: utf-8
from __future__ import unicode_literals

import json
import re
import random
import urllib.parse
from requests import Session

from .common import InfoExtractor
from ..utils import (
    HEADRequest, multipart_encode,
    ExtractorError,
    clean_html,
    get_element_by_class,
    std_headers
)

class FraternityxBaseIE(InfoExtractor):
    _LOGIN_URL = "https://fraternityx.com/sign-in"
    _SITE_URL = "https://fraternityx.com"
    _LOG_OUT = "https://fraternityx.com/sign-out"
    _MULT_URL = "https://fraternityx.com/multiple-sessions"
    _ABORT_URL = "https://fraternityx.com/multiple-sessions/abort"
    _AUTH_URL = "https://fraternityx.com/authorize2"
    _NETRC_MACHINE = 'fraternityx'
    _USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:82.0) Gecko/20100101 Firefox/82.0"

    def __init__(self):
        #self.session = Session()
        std_headers['User-Agent'] = self._USER_AGENT
        self.headers = dict()
        self.headers.update({
            "User-Agent": self._USER_AGENT,
            "Accept-Charset": "",
            "Accept-Encoding" : "gzip, deflate, br",
            "Accept-Language" : "es-ES,en-US;q=0.7,en;q=0.3",
            "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
       

    def _login(self):
        self.username, self.password = self._get_login_info()

        self.report_login()
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
        self._download_webpage_handle(
            self._SITE_URL,
            None,
            'Downloading site page',
            headers=self.headers
        )
        self.headers.update({"Referer" : "https://fraternityx.com/episodes/1"})
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
            "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
            
        }

        boundary = "-------------------------------" + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999))
        
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
            out, content = multipart_encode(data, "-------------------------------"
                + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999)))
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
            self.headers.update({
                "Referer": self._MULT_URL,
            })
            abort_page, url_handle = self._download_webpage_handle(
                self._ABORT_URL,
                None,
                "Log in ok after abort sessions",
                headers=self.headers
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

            content, _ = self._download_webpage_handle(url, None, headers=self.headers)
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
            if re.search(regex_emurl, content):
                embedurl = re.search(regex_emurl, content).group("embedurl")
            if not embedurl:
                raise ExtractorError("", cause="Can't find any video", expected=True)
            
            self.headers.update({'Referer' : url})
            content, _ = self._download_webpage_handle(embedurl, None, headers=self.headers)
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

            #self.session.headers['Referer'] = embedurl
            self.headers.update({
                "Referer" : embedurl,
                "Accept" : "*/*",
                "X-Requested-With" : "XMLHttpRequest"})
            info = self._download_json(videourl, None, headers=self.headers)
            #info = json.loads(self.session.request("GET", videourl).text)

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



class FraternityxIE(FraternityxBaseIE):
    IE_NAME = 'fraternityx'
    IE_DESC = 'fraternityx'
    _VALID_URL = r"https?://(?:www\.)?fraternityx.com/episode/"
    

    def _real_initialize(self):
        self._login()
        self.headers.update({            
            "Referer" : "https://fraternityx.com/episodes/1",
        })

    def _real_extract(self, url):
        data = self._extract_from_page(url)
        #self._log_out()
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(str(data['cause']))
        else:
            return(data)

# class FraternityxPlayListIE(FraternityxBaseIE):
#     IE_NAME = 'fraternityx:playlist'
#     IE_DESC = 'fraternityx:playlist'
#     _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes/(?P<id>\d+)"
#     _BASE_URL = "https://fraternityx.com"

#     def _real_initialize(self):
#         self._login()
#         self.headers.update({
#             "Referer" : self._LOGIN_URL,
#         })

#     def _real_extract(self, url):

#         playlistid = re.search(self._VALID_URL, url).group("id")

  
#         #self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
#         content, _ = self._download_webpage_handle(url, None, headers=self.headers)
#         #page = (webpage.read()).decode('utf-8')
#        # page = self.session.request("GET", url).text
    
#         generic_link = re.compile(r'(?<=\")/episode/[^\"]+(?=\")', re.I)

#         target_links = list(set(re.findall(generic_link, content)))

#         entries = []
#         for link in target_links:
            
#             full_link = self._BASE_URL + link
#             self.headers['Referer'] = url
#             info = self._extract_from_page(full_link)
#             if info:
#                 if not "error" in info['id']:
#                     entries.append(info)
            
#         #self._log_out()
#         return self.playlist_result(entries, "fraternityx Episodes:" + playlistid, "fraternityx Episodes:" + playlistid)

class FraternityxPlayListIE(FraternityxBaseIE):
    IE_NAME = 'fraternityx:playlist'
    IE_DESC = 'fraternityx:playlist'
    _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes/(?P<id>\d+)"
    _BASE_URL = "https://fraternityx.com"

    def _real_initialize(self):
        self._login()
        self.headers.update({
            "Referer" : self._LOGIN_URL,
        })

    def _real_extract(self, url):

        playlistid = re.search(self._VALID_URL, url).group("id")

  
        #self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
        content, _ = self._download_webpage_handle(url, None, headers=self.headers)
        #page = (webpage.read()).decode('utf-8')
       # page = self.session.request("GET", url).text
    
        generic_link = re.compile(r'(?<=\")/episode/[^\"]+(?=\")', re.I)

        target_links = list(set(re.findall(generic_link, content)))

        entries = []
        for link in target_links:
            
            
            entries.append(self.url_result(self._BASE_URL + link, ie=FraternityXIE.ie_key()))
            
            # full_link = self._BASE_URL + link
            # self.headers['Referer'] = url
            # info = self._extract_from_page(full_link)
            # if info:
            #     if not "error" in info['id']:
            #         entries.append(info)
            
        #self._log_out()
        return self.playlist_result(entries, "fraternityx Episodes:" + playlistid, "fraternityx Episodes:" + playlistid)