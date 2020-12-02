# coding: utf-8
from __future__ import unicode_literals

import re
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    ExtractorError,
    sanitize_filename)

class EricVideosIE(InfoExtractor):
    IE_NAME = 'ericvideos'
    IE_DESC = 'ericvideos'
    _VALID_URL = r"https?://(?:www\.)?ericvideos.com"
    _LOGIN_URL = "https://www.ericvideos.com/login.php"
    _SITE_URL = "https://ericvideos.com"
    _LOG_OUT = "https://www.ericvideos.com/logout.php"
    _AUTH_URL = "https://www.ericvideos.com/ES/identification/1/"
    _NETRC_MACHINE = 'ericvideos'


    def _login(self):
        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)


        data = {
            "log_email": username,
            "log_pwd": password,
            "on_submit_ident": '1',
            "back": "https://www.ericvideos.com/ES/compte/1/",
            "lang": 'ES',
            "identifie": ''
        }

        boundary = "-----------------------------" + str(random.randrange(1111111111111111111111111111, 9999999999999999999999999999))
        
        out, content = multipart_encode(data, boundary)
        #print(out)
        #print(content)
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Login request',
            data=out,
            headers={
                "Referer": self._AUTH_URL,
                "Origin": self._SITE_URL,
                "Content-type": content
            }
        )
        #cookies = self._get_cookies(self._LOGIN_URL)
        #print(cookies)



        
    def _log_out(self):
        self._request_webpage(
            self._LOG_OUT,
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
            regex_file = r"\"file\": \"(?P<embedurl>.*?)\""
            regex_id = r"\"mediaid\": \"(?P<mediaid>.*?)\""
            mobjtitle = re.search(regex_title, content)
            mobj = re.search(regex_file, content)
            mobjid = re.search(regex_id, content)
            embedurl = ""
            title = ""
            mediaid = ""
            if mobj:
                embedurl = mobj.group("embedurl")
                if (embedurl == ""):
                    raise Exception(e)
            else:
                raise Exception(e)
            if mobjtitle:
                title = mobjtitle.group("title")
            if mobjid:
                mediaid = mobjid.group("mediaid")

        except Exception as e:
            self._log_out()
            raise ExtractorError("Can't find any video", expected=True)

        
        #print(embedurl)
        
        #print(title)

        #print(self._get_cookies(embedurl))

        try:
            
            formats_m3u8 = self._extract_m3u8_formats(
                embedurl, mediaid, m3u8_id="hls", ext='mp4', entry_protocol='m3u8_native', fatal=False
            )

            self._sort_formats(formats_m3u8)

            #print(formats_m3u8)

            self._log_out()
            
        
        except Exception as e:
            self._log_out()
            raise ExtractorError("Fallo al recuperar ficheros descriptores del vídeo", expected=True)
            
        return {
            "id": mediaid,
            "title": sanitize_filename(title,restricted=True),
            "formats": formats_m3u8,
        }
