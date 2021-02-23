# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError, NO_DEFAULT, urlencode_postdata,
    sanitize_filename
)

class NakedSwordBaseIE(InfoExtractor):
    IE_NAME = 'nakedsword'
    IE_DESC = 'nakedsword'
    
    _SITE_URL = "https://nakedsword.com/"
    _LOGIN_URL = "https://www.nakedsword.com/signin"
    _LOGOUT_URL = "https://nakedsword.com/signout"
    _NETRC_MACHINE = 'nakedsword'

    
    def islogged(self):
        page, urlh = self._download_webpage_handle(
            self._SITE_URL,
            None
        )
        return ("/signout" in page)
    
    def _login(self):
        username, password = self._get_login_info()
        # print(username)
        # print(password)
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
            
        self.report_login()
        login_form = {
            "SignIn_login": username,
            "SignIn_password": password,
            "SignIn_returnUrl": "https://www.nakedsword.com/specialoffers",
            "SignIn_isPostBack": "true",
        }

        # print(login_form)

        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            note="Logging in",
            errnote="Login fail",
            data=urlencode_postdata(login_form),
            headers={
                "Referer": self._LOGIN_URL,
                "Origin": "https://www.nakedsword.com",
                "Upgrade-Insecure-Requests": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "Connection": "keep-alive",
            },
        )

        if url_handle.geturl() == self._LOGIN_URL:
            self.report_warning("Unable to login")
            return False

    def _logout(self):
        self._request_webpage(
            self._LOGOUT_URL,
            None,
            'Log out'
        )


class NakedSwordSceneIE(NakedSwordBaseIE):
    IE_NAME = 'nakedsword:scene'
    _VALID_URL = r"https?://(?:www\.)?nakedsword.com/movies/(?P<movieid>[\d]+)/(?P<title>[a-zA-Z\d_-]+)/scene/(?P<id>[\d]+)/?$"

    def _real_initialize(self):
        if not self.islogged():
            self._login()

    def _real_extract(self, url):

        
        webpage = self._download_webpage(url, None, "Downloading web page scene")
       
        regex_sceneid = r"<meta name='SCENEID' content='(?P<sceid>.*?)'"
        mobj = re.search(regex_sceneid, webpage)
        scene_id = None
        if mobj:
            scene_id = mobj.group("sceid")
            if scene_id:
                getstream_url_m3u8 = "https://www.nakedsword.com/scriptservices/getstream/scene/" + scene_id + "/HLS"
            else:
                raise ExtractorError("Can't find sceneid")
        else:
            raise ExtractorError("Can't finf sceneid")
        
        #print(getstream_url_m3u8)

        mobj = re.match(self._VALID_URL, url)
        
        title_id = mobj.group('id')

        try:

            info_m3u8 = self._download_json(
                    getstream_url_m3u8,
                    scene_id,
                )

            mpd_url_m3u8 = info_m3u8.get("StreamUrl")


            formats_m3u8 = self._extract_m3u8_formats(
                mpd_url_m3u8, scene_id, m3u8_id="hls", ext="mp4", entry_protocol='m3u8_native', fatal=False
            )


                
            n = len(formats_m3u8)
            for f in formats_m3u8:
                f['format_id'] = "hls-" + str(n-1)
                n = n - 1

            title = info_m3u8.get("Title", "nakedsword")
            title = sanitize_filename(title, True)
            title = title + "_scene_" + title_id

            self._logout()
        
        except Exception as e:
            raise ExtractorError from e

        return {
            "id": scene_id,
            "title": title,
            "formats": formats_m3u8,
            "ext": "mp4"
        }

class NakedSwordMovieIE(NakedSwordBaseIE):
    IE_NAME = 'nakedsword:movie'
    _VALID_URL = r"https?://(?:www\.)?nakedsword.com/movies/(?P<id>[\d]+)/(?P<title>[a-zA-Z\d_-]+)/?$"
    _MOVIES_URL = "https://nakedsword.com/movies/"

    def _real_initialize(self):

        self._login()


    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)
        
        playlist_id = mobj.group('id')
        title = mobj.group('title')

        webpage = self._download_webpage(url, playlist_id, "Downloading web page playlist")

        #print(webpage)

        pl_title = self._html_search_regex(r'(?s)<title>(?P<title>.*?)<', webpage, 'title', group='title').split(" | ")[1]

        #print(title)

        scenes_paths = re.findall(rf'{title}/scene/([\d]+)', webpage)

        #print(scenes_paths)

        entries = []
        for scene in scenes_paths:
            entry = self.url_result(self._MOVIES_URL + playlist_id + "/" + title + "/" + "scene" + "/" + scene, 'NakedSwordScene')
            entries.append(entry)

        #print(entries)

        self._logout()

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': sanitize_filename(pl_title, True),
            'entries': entries,
        }

class NakedSwordMostWatchedIE(NakedSwordBaseIE):
    IE_NAME = "nakedsword:mostwatched"
    _VALID_URL = r'https?://(?:www\.)?nakedsword.com/most-watched/?'
    _MOST_WATCHED = 'https://nakedsword.com/most-watched?content=Scenes&page='
    
    def _real_extract(self, url):      
       

        entries = []

        for i in range(1,5):
               
            webpage = self._download_webpage(f"{self._MOST_WATCHED}{i}", None, "Downloading web page playlist")
            if webpage:  
                #print(webpage)          
                videos_paths = re.findall(
                    r"<div class='SRMainTitleDurationLink'><a href='/([^\']+)'>",
                    webpage)     
                
                if videos_paths:

                    for j, video in enumerate(videos_paths):
                        
                        entry = self.url_result(self._SITE_URL + video, 'NakedSwordScene') 
                        entries.append(entry)
                else:
                    raise ExtractorError("No info")


                
            else:
                raise ExtractorError("No info")

                

        return {
            '_type': 'playlist',
            'id': "NakedSWord mostwatched",
            'title': "NakedSword mostwatched",
            'entries': entries,
        }


class NakedSwordStarsIE(NakedSwordBaseIE):
    IE_NAME = "nakedsword:stars"
    _VALID_URL = r'https?://(?:www\.)?nakedsword.com/(?P<typepl>(?:stars|studios))/(?P<id>[\d]+)/(?P<name>[a-zA-Z\d_-]+)/?$'
    _MOST_WATCHED = "?content=Scenes&sort=MostWatched&page="
    _NPAGES = {"stars" : 1, "studios" : 1}
    
    def _real_extract(self, url):      
       
        
        data_list = re.search(self._VALID_URL, url).group("typepl", "id", "name")
        
        entries = []

        for i in range(self._NPAGES[data_list[0]]):


            webpage = self._download_webpage(f"{url}{self._MOST_WATCHED}{i+1}", None, "Downloading web page playlist")
            if webpage:  
                #print(webpage)          
                videos_paths = re.findall(
                    r"<div class='SRMainTitleDurationLink'><a href='/([^\']+)'>",
                    webpage)     
                
                if videos_paths:

                    for j, video in enumerate(videos_paths):
                        
                        entry = self.url_result(self._SITE_URL + video, 'NakedSwordScene') 
                        entries.append(entry)
                else:
                    raise ExtractorError("No info")

                if not "pagination-next" in webpage: break
                
            else:
                raise ExtractorError("No info")

                

        return {
            '_type': 'playlist',
            'id': data_list[1],
            'title':  f"NSw{data_list[0].capitalize()}_{''.join(w.capitalize() for w in data_list[2].split('-'))}",
            'entries': entries,
        }