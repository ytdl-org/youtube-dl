# coding: utf-8
from __future__ import unicode_literals

import re
import random
import urllib.parse
import pprint
from bs4 import BeautifulSoup

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    url_or_none,
    str_or_none
)

class FilminIE(InfoExtractor):

    IE_NAME = 'filmin'
    IE_DESC = 'filmin'
    _VALID_URL = r"https?://(?:www\.)?filmin.es"
    _LOGIN_URL = "https://www.filmin.es/entrar"
    _AUTH_URL = "https://www.filmin.es/login"
    _SITE_URL = "https://www.filmin.es"
    _MEDIAMARKS_URL = "https://bm.filmin.es/mediamarks"
    _NETRC_MACHINE = 'filmin'
    _USER_AG = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) Gecko/20100101 Firefox/79.0"

    def _real_initialize(self):
        self._login()

    def _login(self):

        username, password = self._get_login_info()
        
        if username and password:
            init_page = self._download_webpage(
                self._LOGIN_URL,
                None,
                note="Downloading loging page",
                errnote="Web site not available",
                fatal=True,
                headers={
                    "User-Agent" : self._USER_AG
                }
                

            )

            #print(init_page)
            hidden_inputs = self._hidden_inputs(init_page)
            #print(hidden_inputs)
        
            data = {
                "username": username,
                "password": password,
                "redirect": hidden_inputs['redirect'],
                "_token": hidden_inputs['_token']
            }

            #print(data)
        
            login_result = self._download_json(
                self._AUTH_URL,
                None,
                note="Requesting login",
                errnote="Unable to login",
                data=urlencode_postdata(data),
                headers={
                    "Referer": self._LOGIN_URL,
                    "Origin": self._SITE_URL,
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent" : self._USER_AG
                },
                fatal=True
            )['status']

            #print(login_result)
        
            if (login_result == 'fail'):
                
                raise ExtractorError("Wrong username and/or password")

        else:
            raise ExtractorError("Missing login inputs")

        self.report_login()

 


    def _real_extract(self, url):
        
        content  = self._download_webpage(
            url,
            None,
            note="Downloading video page",
            errnote="Unable to download video page",
            fatal=True,
            headers={
                "Referer": self._SITE_URL,
                "Upgrade-Insecure-Requests": "1",
                "User-Agent" : self._USER_AG
            },
        )

        #print(content)

        hidden_inputs = self._hidden_inputs(content)
        #print(hidden_inputs)

        res = BeautifulSoup(content, "html5lib")
        
        #print(res)
        # tag = res.find("a", {"class": "premium view main-action-btn tmp-fx-fade-player"})
        # print(tag)
        # video_url = tag["href"]

        # tag = res.find("button", {"class": "btn-regular js-like-btn"})
        # video_type = tag["data-type"]
        # media_id = tag["data-id"]

        tag = res.find("a", {"class" : "Button Button--block Button--xl Button--accent"})
        #print(tag)
        video_url = tag['href']

        content  = self._download_webpage(
            video_url,
            None,
            note="Downloading video page",
            errnote="Unable to download video page",
            fatal=True,
            headers={
                "Referer": url,
                "User-Agent" : self._USER_AG
            },
        )

        #print(content)

        media_id = video_url.split('&mediaId=')[1]
        video_type = video_url.split('&mediaId=')[0].split('type=')[1]

        #print(media_id)
        #print(video_type)       

        video_json_url = self._SITE_URL + "/player/data/" + video_type + "/" + media_id
        
        info_video = self._download_json(
                video_json_url,
                None,
                note="Requesting JSON",
                errnote="Unable to get JSON",
                headers={
                    "Referer": video_url,
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent" : self._USER_AG
                },
                fatal=True
            )

        #versión VOS
        title = info_video['media']['title']
        for version in info_video['media']['versions']:
            if version['version_type']['lang'] == "VOS":
                version_id = version['id']
        
        
        version_json_url = video_json_url + "/" + str(version_id)
        #print(version_json_url)

        info_version = self._download_json(
                version_json_url,
                None,
                note="Requesting JSON version",
                errnote="Unable to get JSON version",
                headers={
                    "Referer": video_url,
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent" : self._USER_AG
                },
                fatal=True
            )
        
        #print.pprint(info_version)

        cookies = self._get_cookies(url)
        session_id = cookies['laravel_session'].value
        #print(session_id)

        mediamark = {
            "token": info_video['mediamark']['token'],
            "position": "0",
            "duration": info_version['duration'],
            "media_id": media_id,
            "version_id": version_id,
            "media_viewing_id": info_version['mediaViewingId'],
            "subtitle_id": "off",
            "next_media_at": "",
            "session_id": session_id,
            "session_connections": "2"
        }


            

        
        info_mediamark = self._download_json(
                self._MEDIAMARKS_URL,
                None,
                data=urlencode_postdata(mediamark),
                headers={
                    "Referer": video_url,
                    "User-Agent" : self._USER_AG
                },
                fatal=True
            )

        #print(info_mediamark)

        url_list = []
        for source in info_version['sources']:
            url_list.append(source['file'])

        print(url_list)

        formats_m3u8 = self._extract_m3u8_formats(
            url_list[0], None, m3u8_id="hls", fatal=False
        )


        content  = self._download_webpage(
            url_list[1],
            None,
            note="Downloading video page",
            errnote="Unable to download video page",
            fatal=True,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )

        print(content)

        formats_dash = self._extract_mpd_formats(
            url_list[2], None, mpd_id="2011", fatal=False
        )

        print(formats_m3u8)


        self._sort_formats(formats_m3u8)
        #self._sort_formats(formats_dash)

        return {
            "id": media_id,
            "title": title,
            #"formats": formats_m3u8 + formats_dash
            "formats" : formats_m3u8
        }