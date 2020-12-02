# coding: utf-8
from __future__ import unicode_literals

import re
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    ExtractorError)

class FraternityxIE(InfoExtractor):
    IE_NAME = 'fraternityx'
    IE_DESC = 'fraternityx'
    _VALID_URL = r"https?://(?:www\.)?fraternityx.com/episode/"
    _LOGIN_URL = "https://fraternityx.com/sign-in"
    _SITE_URL = "https://fraternityx.com"
    _LOG_OUT_URL = "https://fraternityx.com/sign-out"
    _MULT_URL = "https://fraternityx.com/multiple-sessions"
    _AUTH_URL = "https://fraternityx.com/authorize2"
    _ABORT_URL = "https://fraternityx.com/multiple-sessions/abort"
    _NETRC_MACHINE = 'fraternityx'


    def _login(self):
        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
        self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
        login_page = self._download_webpage(
            self._SITE_URL,
            None,
            'Downloading site page'
        )
        
        cookies = self._get_cookies(self._LOGIN_URL)
        #print(cookies)
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
            'Login request',
            data=out,
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                #"Upgrade-Insecure-Requests": "1",
                "Content-Type": content,
                #"Connection": "keep-alive",
            }
        )

        if ((url_handle.geturl() == self._SITE_URL) or (url_handle.geturl() == self._SITE_URL + "/episodes/1")):
            return
        elif (url_handle.geturl() == self._LOGIN_URL):
            raise ExtractorError("Fails username/password", expected=True)
        elif (url_handle.geturl() == self._MULT_URL):
            abort_page, url_handle = self._download_webpage_handle(
                self._ABORT_URL,
                None,
                "Log in ok after abort sessions",
                headers={
                    "Referer": self._MULT_URL}
            )
            return
        elif (url_handle.geturl() == self._AUTH_URL):
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
                    "Content-Type": content
                }
            )
            if ((url_handle.geturl() == self._SITE_URL) or (url_handle.geturl() == self._SITE_URL + "/episodes/1")):
                return
            elif (url_handle.geturl() == self._MULT_URL):
                abort_page, url_handle = self._download_webpage_handle(
                    self._ABORT_URL,
                    None,
                    "Log in ok after abort sessions",
                    headers={
                        "Referer": self._MULT_URL
                    }
                )
                return
            else:
                raise ExtractorError("Fails auth2: " + url_handle.geturl(), expected=True)

    def _log_out(self):
        self._request_webpage(
            self._LOG_OUT_URL,
            None,
            'Log out'
        )

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):

        try:

            #print(self._get_cookies(url))

            content, url_handle = self._download_webpage_handle(
                url,
                None,
                'Downloading video page'
            )
            #print(content)
            regex_title = r"<title>(?P<title>.*?)</title>"
            regex_token = r"iframe src=\"(?P<embedurl>.*?)\""
            mobjtitle = re.search(regex_title, content)
            mobj = re.search(regex_token, content)
            embedurl = ""
            title = ""
            if mobj:
                embedurl = mobj.group("embedurl")
                if (embedurl == ""):
                    raise Exception(e)
            else:
                raise Exception(e)
            if mobjtitle:
                title = mobjtitle.group("title")

        except Exception as e:
            self._log_out()
            raise ExtractorError("Can't find any video", expected=True)

        
        #print(embedurl)
        
        #print(title)

        #print(self._get_cookies(embedurl))

        try:

            #conseguimos el token para el video
            
            content, url_handle = self._download_webpage_handle(
                embedurl,
                None,
                'Downloading embed video'
            )
            
            #print(self._get_cookies(embedurl))
            #print(content)
            regex_token = r"token: '(?P<tokenid>.*?)'"
            mobj = re.search(regex_token, content)
            tokenid = ""
            if mobj:
                tokenid = mobj.group("tokenid")
                if (tokenid == ""):
                    raise Exception(e)
            else:
                raise Exception(e)
                
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            #print(videourl)

            info = self._download_json(
                videourl,
                None,
                'JSON file',
                headers={
                    "Accept": "*/*",
                    "Referer": embedurl,
                    "Upgrade-Insecure-Requests": "1",
                    "Connection": "keep-alive",
                }
            )
            #print(info)
            manifesturl = "https://videostreamingsolutions.net/api:ov-embed/manifest/" + info['xdo']['video']['manifest_id'] + "/manifest.m3u8"
            
            
            formats_m3u8 = self._extract_m3u8_formats(
                manifesturl, None, m3u8_id="hls", fatal=False
            )

            self._sort_formats(formats_m3u8)

            
            self._log_out()
        
        except Exception as e:
            self._log_out()
            raise ExtractorError("Fallo al recuperar ficheros descriptores del vídeo", expected=True)
            
        return {
            "id":str(info['xdo']['video']['id']),
            "title": title,
            "formats": formats_m3u8
        }

class FraternityxPlayListIE(InfoExtractor):
    IE_NAME = 'fraternityx:playlist'
    IE_DESC = 'fraternityx:playlist'
    _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes/(?P<id>)"
    _BASE_URL = "https://fraternityx.com"




    def _real_extract(self, url):

        playlistid = url.split('episodes/')[1]

        print(playlistid)
        self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
        page = self._download_webpage(
            url,
            None,
            'Downloading page of episodes'
        )

        generic_link = re.compile(r'(?<=\")/episode/.+(?=\")', re.I)

        target_links = list(set(re.findall(generic_link, page)))
     
        entries = []
        for link in target_links:
            
            full_link = self._BASE_URL + link
 
            title = link.split('episode/')[1].replace("-", " ")

            entries.append({
                "_type": "url",
                "url": full_link,
                "title": title,
            })

        return self.playlist_result(entries, "FraternityX Episodes:" + playlistid, "FraternityX Episodes:" + playlistid)

