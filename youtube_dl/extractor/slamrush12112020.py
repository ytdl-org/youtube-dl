# coding: utf-8
from __future__ import unicode_literals

import re
from bs4 import BeautifulSoup
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    ExtractorError)
from html5print import HTMLBeautifier


class SlamRushPlaylistIE(InfoExtractor):
    IE_NAME = 'slamrush:playlist'
    _VALID_URL = r"https?://(?:www\.)?slamrush.com"
    _LOGIN_URL = "https://slamrush.com/sign-in"
    _LOG_OUT_URL = "https://slamrush.com/sign-out"
    _SITE_URL = "https://slamrush.com"
    _ENTER_URL = "https://slamrush.com/enter"
    _WARNING_URL = "https://slamrush.com/warning"
    _AUTH_URL = "https://slamrush.com/authorize2"
    _ABORT_URL = "https://slamrush.com/multiple-sessions/abort"
    _MULT_URL = "https://slamrush.com/multiple-sessions"
    _NETRC_MACHINE = 'slamrush'

    def _login(self):

        username, password = self._get_login_info()
        #print(username)
        #print(password)

        #username, password = self._get_netrc_login_info(self._NETRC_MACHINE)

        print(username)
        print(password)

        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
        self._set_cookie('slamrush.com', 'pp-accepted', 'true')
        login_page = self._download_webpage(
            self._SITE_URL,
            None,
            'Downloading site page'
        )

        cookies = self._get_cookies(self._LOGIN_URL)
        data = {
            "username": username,
            "password": password,
            "_csrf-token": urllib.parse.unquote(cookies['X-EMA-CSRFToken'].coded_value)
        }

        
        boundary = "-------------------------------" + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999))
        
        out, content = multipart_encode(data, boundary)
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Log in request',
            data=out,
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                #"Upgrade-Insecure-Requests": "1",
                "Content-Type": content,
                #"Connection": "keep-alive",
            }
        )

        #print("69: " + url_handle.geturl())
        if ((url_handle.geturl() == self._SITE_URL) or (url_handle.geturl() == (self._SITE_URL + "/"))):
            #print("OKOKOK")
            return

        elif (url_handle.geturl() == self._LOGIN_URL):
            raise ExtractorError("Fails username/password", expected=True)
        
        elif (url_handle.geturl() == self._MULT_URL):
            abort_page, url_handle = self._download_webpage_handle(
                self._ABORT_URL,
                None,
                headers={
                    "Referer": self._MULT_URL,
                }
            )
            #print("84: " + url_handle.geturl())
            #print("OKOKOK")

            return
        
        elif (url_handle.geturl() == self._AUTH_URL):

            cookies2 = self._get_cookies(self._AUTH_URL)
            data2 = {
                "email": "a.tgarc@gmail.com",
                "last-name": "Torres",
                "_csrf-token": urllib.parse.unquote(cookies2['X-EMA-CSRFToken'].coded_value)
            }

            out2, content2 = multipart_encode(data2, boundary)

            auth_page, url_handle = self._download_webpage_handle(
                self._AUTH_URL,
                None,
                data=out2,
                headers={
                    "Referer": self._AUTH_URL,
                    "Origin": self._SITE_URL,
                    "Content-Type": content2                    
                }
            )
            #print("108: " + url_handle.geturl())
            if ((url_handle.geturl() == self._SITE_URL) or (url_handle.geturl() == (self._SITE_URL + "/"))):
                #print("OKOKOK")
                return
            elif (url_handle.geturl() == self._MULT_URL):
                abort_page, url_handle = self._download_webpage_handle(
                    self._ABORT_URL,
                    None,
                    headers={
                        "Referer": self._MULT_URL,
                    }
                )
                #print("119: " + url_handle.geturl())
                if ((url_handle.geturl() == self._SITE_URL) or (url_handle.geturl() == (self._SITE_URL + "/"))):
                    #print("OKOKOK")
                    return
                else:
                    raise ExtractorError("Fails username/password", expected=True)
        
            else:
                raise ExtractorError("Fails username/password", expected=True)

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
    

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        content = self._download_webpage(url, "Searching for videos in SlamRush web page")
        bs = BeautifulSoup(content, "html5lib")
        divs = bs.find_all("div", {"class": "episode-item"})
        embedurl_list = []
        video_name_list = []
        for div in divs:
            ep = div.get('data-bind')
            #print(ep)
            embedurl = (ep.replace('episodePlayer: ', ''))[1:-1]
            if embedurl:
                #print(embedurl)
                embedurl_list.append(embedurl)
            n = div.find("div", {"class": "name"}).getText()
            if n:
                video_name = n.strip()
                #print(video_name)
                video_name_list.append(video_name)

        manifesturl_list = []
        formats_m3u8_list = []
        info_list = []
        id_list = []
        

        for embedurl in embedurl_list:

            content = self._download_webpage(
                embedurl,
                None,
                headers={
                    "Referer": self._SITE_URL                       
                }
            )
            
            #print(content)
            #cookies3 = self._get_cookies(embedurl)
            #print(cookies3)
            regex_token = r"token: '(?P<tokenid>.*?)'"
            mobj = re.search(regex_token, content)
            tokenid = mobj.group("tokenid")
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            info = self._download_json(videourl, None)
            id_list.append(info['xdo']['video']['id'])
            info_list.append(info)
            manifesturl = "https://videostreamingsolutions.net/api:ov-embed/manifest/" + info['xdo']['video']['manifest_id'] + "/manifest.m3u8"
            manifesturl_list.append(manifesturl)

            #print(manifesturl)

            formats_m3u8 = self._extract_m3u8_formats(
                 manifesturl, None, m3u8_id="hls", fatal=False
            )

            self._sort_formats(formats_m3u8)
            formats_m3u8_list.append(formats_m3u8)
            

        self._log_out()
        entries = []
        i = 0
        for i in range(len(video_name_list)):

            entries.append({
                "_type" : "video",
                "id" :  str(id_list[i]),
                "title" : video_name_list[i],
                #"url" : manifesturl_list[i],
                "formats" : formats_m3u8_list[i]
            })
        
        
        return self.playlist_result(entries, "SlamRush Episodes", "SlamRush Episodes")
