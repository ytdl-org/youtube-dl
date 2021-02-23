from __future__ import unicode_literals


import re
from .common import InfoExtractor
from .streamtape import StreamtapeIE
from ..utils import (
    urlencode_postdata,
    HEADRequest,
    std_headers,
    sanitize_filename
)

class MyVidsterBaseIE(InfoExtractor):

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

class MyVidsterIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/(?:video|vsearch)/(?P<id>\d+)/?(?:.*|$)'

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



    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace("vsearch", "video")
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        real_url = self._html_search_regex(r'rel="videolink" href="(?P<real_url>.*)">',
            webpage, 'real_url')

        #self.to_screen(f"{real_url}")   

        if real_url.startswith("https://www.myvidster.com/video"):
            
            webpage = self._download_webpage(real_url, video_id)
            str_regex = r'source src="(?P<video_url>.*)" type="video'
            mobj = re.search(str_regex, webpage)

                        
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
                    'format_id' : 'http-mp4',
                    'url' : video_url,
                    'filesize' : filesize,
                    'ext' : 'mp4'
                }
            
                entry_video = {
                    'id' : video_id,
                    'title' : title,
                    'formats' : [format_video],
                    'ext': 'mp4'
                }
                
                return entry_video


        else:

            entry_video = {
                '_type' : 'url_transparent',
                'url' : real_url,
                'id' : video_id,
                'title' : title
            }

            return entry_video


class MyVidsterChannelIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster:channel'
    #_VALID_URL = r'https?://(?:www\.)?myvidster\.com/channel/(?P<id>\d+)/?(?:.*|$)'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/channel/(?P<id>\d+).*'
    _POST_URL = "https://www.myvidster.com/processor.php"
 

    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_extract(self, url):
        channelid = self._match_id(url)
        webpage = self._download_webpage(url, channelid, "Downloading main channel web page")
        title = self._search_regex(r'<title>([\w\s]+)</title>', webpage, 'title', default=f"MyVidsterChannel_{channelid}", fatal=False)
        
        num_videos = self._search_regex(r"display_channel\(.+,(\d+)\)", webpage, 'number of videos')

        info = {
            'action' : 'display_channel',
            'channel_id': channelid,
            'page' : 1,
            'thumb_num' : num_videos,
            'count' : num_videos
        }

        webpage, ulrh = self._download_webpage_handle(
            self._POST_URL,
            channelid,
            None,
            None,
            data=urlencode_postdata(info),
            headers={'Referer' : url, 'Accept' : '*/*', 'x-requested-with' : 'XMLHttpRequest', 'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        )

        list_videos = re.findall(r'<a href=\"(/video/[^\"]+)\" class', webpage)

        entries = [self.url_result(f"{self._SITE_URL}{video}", "MyVidster") for video in list_videos]


        return {
            '_type': 'playlist',
            'id': channelid,
            'title': sanitize_filename(title, True),
            'entries': entries,
        }


