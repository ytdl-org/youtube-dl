# coding: utf-8
from __future__ import unicode_literals

import re
from bs4 import BeautifulSoup

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    clean_html
)
import urllib.parse

from bs4 import BeautifulSoup

import pprint

from html5print import HTMLBeautifier

class TetatitaIE(InfoExtractor):

    IE_NAME = 'tetatita'
    IE_DESC = 'tetatita'
    _VALID_URL = r"https?://(?:www\.)?tetatita.com"
    _LOGIN_URL = "https://www.tetatita.com/login"
    _AUTH_URL = "https://www.tetatita.com/library/ajax/login.php?"
    _SITE_URL = "https://www.tetatita.com"
    _NETRC_MACHINE = 'tetatita'
    _VIDEOS_URL = "https://www.tetatita.com/page/"

    def _real_initialize(self):
        self._login()

    def _login(self):

        username, password = self._get_login_info()
        
        if username and password:
            
            urlh = self._request_webpage(
                self._SITE_URL, None
            )
            auth_url = self._AUTH_URL + urllib.parse.unquote("email=" + username + "&password=" + password)

            content = self._download_json(
                auth_url, None
            )

            #print(content)
            if (content != 3):
                return
 

        i = 0

        while (i < 26):
            try:
                i = i + 1
                #print(str(i))
                content = self._download_webpage(self._VIDEOS_URL + str(i), "Analizando web page")
                #print(content)
                    
                bs = BeautifulSoup(content, "html5lib")
                divs = bs.findAll("div", {"class": "project-item-inner"})
                for div in divs:
                    tag = div.find("a")
                    print(self._SITE_URL + "/" + tag.get("href"))
            
            except Exception:
                print('Final web scraping')
            
        return
