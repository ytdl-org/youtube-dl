from __future__ import unicode_literals

from .common import InfoExtractor
from .streamtape import StreamtapeIE
from ..utils import (
    urlencode_postdata,
    HEADRequest,
    std_headers
)

import re

class MyVidsterIE(InfoExtractor):
    IE_NAME = 'myvidster'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/video/(?P<id>\d+)/?(?:.*|$)'

    _TEST = {
        'url': 'http://www.myvidster.com/video/32059805/Hot_chemistry_with_raw_love_making',
        'md5': '95296d0231c1363222c3441af62dc4ca',
        'info_dict': {
            'id': '3685814',
            'title': 'md5:7d8427d6d02c4fbcef50fe269980c749',
            'upload_date': '20141027',
            'uploader': 'utkualp',
            'ext': 'mp4',
            'age_limit': 18,
        },
        'add_ie': ['XHamster'],
    }

    _LOGIN_URL = "https://www.myvidster.com/user/"
    _SITE_URL = "https://www.myvidster.com"
    _NETRC_MACHINE = "myvidster"

    def _log_in(self):
        
        self.username, self.password = self._get_login_info()

        self.report_login()
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
               

        data = {
            "user_id": self.username,
            "password": self.password,
            "save_login" : "on",
            "submit" : "Log+In",
            "action" : "log_in"
        }

        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            note="Logging in",
            errnote="Login fail",
            data=urlencode_postdata(data),
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        if not "action=log_out" in login_page:
            self.raise_login_required(
                'Log in failed')


    def islogged(self):
        
        webpage, _ = self._download_webpage_handle(self._LOGIN_URL, None)
        return("action=log_out" in webpage)

    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        real_url = self._html_search_regex(r'rel="videolink" href="(?P<real_url>.*)">',
            webpage, 'real_url')

        self.to_screen(f"{real_url}")   

        if real_url.startswith("https://www.myvidster.com/video"):
            
            webpage = self._download_webpage(real_url, video_id)
            str_regex = r'source src="(?P<video_url>.*)" type="video'
            mobj = re.search(str_regex, webpage)
            #print(webpage)
                        
            if mobj:
                video_url = mobj.group('video_url')

                std_headers['Referer'] = url
                std_headers['Accept'] = "*/*"
                reqhead = HEADRequest(video_url)
                res = self._request_webpage(reqhead, None, headers={'Range' : 'bytes=0-'})
                filesize = res.getheader('Content-Lenght')
                if filesize:
                    filesize = int(filesize)    

                format_video = {
                    'format_id' : "http-mp4",
                    'url' : video_url,
                    'filesize' : filesize
                }
            
                entry_video = {
                    'id' : video_id,
                    'title' : title,
                    'formats' : [format_video],
                    'ext': "mp4"
                }
                
                return entry_video

        # streamtape_url = StreamtapeIE._extract_url(webpage)
        # #print(f"streamtape url: {streamtape_url}")
        # if streamtape_url:
            
        #     entry_video = StreamtapeIE._extract_info_video(streamtape_url, video_id)
        #     #print(entry_video)
        #     entry_video['title'] = title
        #     #print(entry_video)
         
        #     return entry_video

        else:
            entry_video = {
                '_type' : 'url_transparent',
                'url' : real_url,
                'id' : video_id,
                'title' : title
            }

            #self.url_result(real_url, None, video_id, title)
            #print(entry_video)
            return entry_video