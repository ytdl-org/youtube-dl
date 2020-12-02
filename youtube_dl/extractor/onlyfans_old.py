# coding: utf-8
from __future__ import unicode_literals

import re
import random
import urllib.parse
import json
import requests

from .common import InfoExtractor
from ..utils import (
    multipart_encode,
    urlencode_postdata,
    ExtractorError)

class OnlyFansIE(InfoExtractor):
    IE_NAME = 'onlyfans'
    IE_DESC = 'onlyfans'
    _VALID_URL = r"https?://(?:www\.)?onlyfans.com"

    _INIT_URL = "https://onlyfans.com/api2/v2/init?app-token=33d57ade8c02dbc5a333db99ff9ae26a"
    _LOGIN_URL = "https://www.onlyfans.com/twitter/auth?"
    _AUTH_URL = "https://api.twitter.com/oauth/authenticate"
    _LOGIN2_URL = "https://onlyfans.com/twitter/callback?"
    
    
    _SITE_URL = "https://onlyfans.com/"
    
    _NETRC_MACHINE = 'twitter2'
    _USER_AG = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) Gecko/20100101 Firefox/79.0"

    def _login(self):
        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        content, url_handle = self._download_webpage_handle(
            self._INIT_URL,
            None,
            'Downloading site page',
            headers={
                "Referer": self._SITE_URL,
                "Accept": "application/json, text/plain, */*",
                "User-Agent" : self._USER_AG,
            }
        )

        ##print(content)
        cookies = self._get_cookies(self._SITE_URL)
        print(cookies)
        csrf = urllib.parse.unquote(cookies['csrf'].coded_value)
        #print(csrf)

        #self._set_cookie('onlyfans.com', "ref_src", "")
        #self._set_cookie('onlyfans.com', "sc_is_visitor_unique", "rx12105524.1596833962.4F2AF4D97D304F1E36A8DC6EF9BBB722.1.1.1.1.1.1.1.1.1")
        self._set_cookie('onlyfans.com', "auth_id", "4090129")
        #self._set_cookie('onlyfans.com', "fp", "946dfbb427079a405b5a414811c4fd51")
        self._set_cookie('onlyfans.com', "wallLayout", "list")
        
        content, url_auth = self._download_webpage_handle(
            self._LOGIN_URL + "csrf=" + csrf,
            None,
            'Auth via twitter'
        )

        #print("+++++++++++56:" + url_auth.geturl())
        #print(content)



        inputs = self._hidden_inputs(content)
        #print(inputs)
        
        data = {
            "authenticity_token": inputs['authenticity_token'],
            "redirect_after_login": inputs['redirect_after_login'],
            "oauth_token": inputs['oauth_token'],
            "session[username_or_email]":username,
            "session[password]": password,
        }

        #print(data)


        content, url_handle = self._download_webpage_handle(
            self._AUTH_URL,
            None,
            'Login request twitter',
            data=urlencode_postdata(data),
            headers={
                "Referer": url_auth.geturl(),
                "Origin": "https://api.twitter.com",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "User-Agent" : self._USER_AG,
            }
        )

        print("+++++++++++85:" + url_handle.geturl())
        #print(content)


        regex_url = r"<meta http-equiv=\"refresh\" content=\"0;url=(?P<url>.*?)\""
        mobj = re.search(regex_url, content)  
        url = ""
        if mobj:
            url = mobj.group("url")
            url = url.replace(';', '=')
            print("++++++++++++++++++92:" + url)
            content, url_handle = self._download_webpage_handle(
                url,
                None,
                'Login request',
                headers={
                    "User-Agent" : self._USER_AG,
                    "TE": "Trailers",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
            )

        

        


    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
 
        try:

            ##print(self._get_cookies(url))
            #print(url)
            #self._set_cookie(self._SITE_URL, 'wallLayout', 'list')
            #print(self._get_cookies(url))

            cont, u = self._download_webpage_handle(
                self._INIT_URL,
                None,
                'Downloading site page',
                headers={
                    "Referer": self._SITE_URL,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "es-ES,en-US;q=0.7,en;q=0.3",
                    #"time": "1596842589976",
                    #"sign": "3fd9a2361befaf850eafc547ae7d6cf1856c6f7e",
                    "User-Agent" : self._USER_AG
                }
            )

            #access_token = req.headers['access-token']

            #print(access_token)
            
            cookies = self._get_cookies(self._SITE_URL)
            print(cookies)
            access_token = cookies['sess'].coded_value
            print(access_token)

            info  = self._download_json(
                "https://onlyfans.com/api2/v2/users/127138/posts/videos?limit=200&order=publish_date_desc&skip_users=all&skip_users_dups=1&pinned=0&app-token=33d57ade8c02dbc5a333db99ff9ae26a",
                None,
                'JSON Files',
                headers={
                    "Referer": url,
                    "access-token": access_token,
                    "user-id": "4090129",
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent" : self._USER_AG,
                    "Accept-Encoding": "gzip, deflate, br",
                    "TE": "Trailers",
                
                }
            )

           #print(info)

            info2 = self._download_json(
                "https://onlyfans.com/api2/v2/users/127138/posts/videos?limit=200&order=publish_date_desc&skip_users=all&skip_users_dups=1&beforePublishTime=1576704242.000000&pinned=0&app-token=33d57ade8c02dbc5a333db99ff9ae26a",
                None,
                'JSON Files',
                headers={
                    "Referer": url,
                    "access-token": access_token,
                    "user-id": "4090129",
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent" : self._USER_AG,
                    "Accept-Encoding": "gzip, deflate, br",
                    "TE": "Trailers",
                
                }
            )
            
            #print(info2)

            with open('info1frosted.json', 'w') as outfile:
                json.dump(info, outfile)

            with open('info2frosted.json', 'w') as outfile:
                json.dump(info2, outfile)


        except Exception as e:
            #self._log_out()
            raise ExtractorError("Can't find any video", expected=True)
        ##print(embedurl)
        
        ##print(title)

        ##print(self._get_cookies(embedurl))

        try:
            
            formats_m3u8 = self._extract_m3u8_formats(
                embedurl, None, m3u8_id="hls", fatal=False
            )

            self._sort_formats(formats_m3u8)

            ##print(formats_m3u8)

            #self._log_out()
            
        
        except Exception as e:
            #self._log_out()
            raise ExtractorError("Fallo al recuperar ficheros descriptores del vídeo", expected=True)
            
        return {
            "id": mediaid,
            "title": title,
            "formats": formats_m3u8
        }
