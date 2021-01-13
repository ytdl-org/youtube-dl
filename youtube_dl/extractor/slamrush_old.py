# coding: utf-8
from __future__ import unicode_literals

import random
import urllib.parse
import re

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    ExtractorError,
    clean_html,
    get_element_by_class)

from requests_html import (
    HTMLSession,
   
)


class SlamRushBaseIE(InfoExtractor):
    _LOGIN_URL = "https://slamrush.com/sign-in"
    _LOG_OUT_URL = "https://slamrush.com/sign-out"
    _SITE_URL = "https://slamrush.com"
    _ENTER_URL = "https://slamrush.com/enter"
    _WARNING_URL = "https://slamrush.com/warning"
    _AUTH_URL = "https://slamrush.com/authorize2"
    _ABORT_URL = "https://slamrush.com/multiple-sessions/abort"
    _MULT_URL = "https://slamrush.com/multiple-sessions"
    _NETRC_MACHINE = 'slamrush'
    _USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/84.0.4147.135 Safari/537.36"
    _API_VIDEO = "https://slamrush.com/api:ov-embed/video/"

    def __init__(self):
        self.session = HTMLSession()
        self.session.headers.update({
            "User-Agent": self._USER_AGENT,
        })
        self.user_agent = self._USER_AGENT

    def islogged(self):

        webpage, _ = self._download_webpage_handle(
            self._SITE_URL,
            None,
            None
        )

        return ("Logout" in webpage)
    def _login(self):

        self.username, self.password = self._get_login_info()
        #print(username)
        #print(password)webpage =
    
        self.report_login()
        
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
        self._set_cookie('slamrush.com', 'pp-accepted', 'true')

        self._download_webpage(
            self._SITE_URL,
            None,
            'Downloading site page',
            # headers={
            #     "User-Agent": self.user_agent,
            # }
                
        )

        self.cookies = self._get_cookies(self._LOGIN_URL)
        #print(self.cookies)
        #print(type(self.cookies))

        data = {
            "username": self.username,
            "password": self.password,
            "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
        }

        
        boundary = "-----------------------------" + str(random.randrange(11111111111111111111111111111, 99999999999999999999999999999))
        
        out, content = multipart_encode(data, boundary)
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Log in request',
            data=out,
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,                #
                "Content-Type": content,
                "User-Agent": self.user_agent
            }
        )

        if self._AUTH_URL in url_handle.geturl():
            data = {
                "email": "a.tgarc@gmail.com",
                "last-name": "Torres",
                "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
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
        logout_page, url_handle = self._download_webpage_handle(
                    self._LOG_OUT_URL,
                    None,
                    'Log out'
                )
        #print("135: " + url_handle.geturl())
        if (url_handle.geturl() == self._MULT_URL):
                abort_page, url_handle = self._download_webpage_handle(
                    self._ABORT_URL,
                    None,
                    headers={
                        "Referer": self._MULT_URL,
                    }
                )
 
class SlamRushIE(SlamRushBaseIE):
    IE_NAME = 'slamrush'
    _API_TOKEN = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token="
    _API_MANIFEST = "https://videostreamingsolutions.net/api:ov-embed/manifest/"
    _VALID_URL = r"https://slamrush.com/api:ov-embed/video/"

    def _real_extract(self, url):

        text = url.split(self._API_VIDEO)[1]
        infotext = text.split("/=?title?=/")
        title = infotext[0]
        #print(title)
        embedurl = infotext[1]
        #print(embedurl)
        vembed_page = self.session.get(embedurl, headers={'Referer' : self._SITE_URL})
        regex_token = r"token: '(?P<tokenid>.*?)'"
        mobj = re.search(regex_token, vembed_page.html.html)
        tokenid = mobj.group("tokenid")
        #print(tokenid)
        info = self._download_json(self._API_TOKEN + tokenid, None)
        #print(info)
        videoid = info['xdo']['video']['id']            
        
        manifestid = info['xdo']['video']['manifest_id']
        manifesturl = self._API_MANIFEST + manifestid + "/manifest.m3u8"

        #print(manifesturl)

        formats_m3u8 = self._extract_m3u8_formats(
                 manifesturl, None, m3u8_id="hls", ext="mp4", entry_protocol="m3u8", fatal=False
            )
        self._sort_formats(formats_m3u8)

        #print(formats_m3u8)

        return({
            "_type" : "video",
            "id" : str(videoid),
            "title" : title,
            "formats" : formats_m3u8,
        }
        )
     



class SlamRushPlaylistIE(SlamRushBaseIE):
    IE_NAME = 'slamrush:playlist'
    _VALID_URL = r"https?://(?:www\.)?slamrush.com"

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
       
        for key, v in self.cookies.items():
            self.session.cookies.set(key, self.cookies[key].coded_value)
        webpage = self.session.get(url)
        episodes = webpage.html.find("div.episode-item")
        entries = []
        for ep in episodes:
            title = ep.text.split('\n')[0]
            vembed_url = ep.attrs['data-bind'].split("episodePlayer: ")[1][1:-1]
                        
            entries.append({
                "_type" : "url",
                "url": self._API_VIDEO + title + "/=?title?=/" + vembed_url,
                "title": title,
                "ie_key" : SlamRushIE.ie_key()

            })
     

        return self.playlist_result(entries, "SlamRush" )
