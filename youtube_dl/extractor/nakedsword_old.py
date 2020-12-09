# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    sanitize_filename
)


class NakedSwordIE(InfoExtractor):
    IE_NAME = 'nakedsword'
    IE_DESC = 'nakedsword'
    _VALID_URL = r"https?://(?:www\.)?nakedsword.com/movies/(?P<id>[^&?#]+)"
    _LOGIN_URL = "https://www.nakedsword.com/signin"
    _LOGOUT_URL = "https://nakedsword.com/signout"
    _NETRC_MACHINE = 'nakedsword'

    def _real_initialize(self):
        self._login()

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

    def _real_extract(self, url):

        try:

            webpage_url = url
            webpage = self._downloader.urlopen(webpage_url)
            content = (webpage.read()).decode('utf-8')

            # print(content)

            regex_movieid = r"<meta name='MOVIEID' content='(?P<movid>.*?)'"
            regex_sceneid = r"<meta name='SCENEID' content='(?P<sceid>.*?)'"
            # regex_movieid = self._meta_regex("MOVIEID")
            # regex_sceneid = self._meta_regex("SCENEID")

            # self._search_regex(pattern, string, name, default, fatal, flags, group)
            # movieid = self._search_regex(regex_movieid, content, "MOVIEID", default=None)
            # sceneid = self._search_regex(regex_sceneid, content, "SCENEID", default=None)
            # print(regex_movieid)
            mobj = re.search(regex_movieid, content)
            movie_id = mobj.group("movid")
            mobj = re.search(regex_sceneid, content)
            if mobj:
                scene_id = mobj.group("sceid")
                # print("sceneid", scene_id)
                #getstream_url = "https://www.nakedsword.com/scriptservices/getstream/scene/" + scene_id + "/DASH"
                getstream_url_m3u8 = "https://www.nakedsword.com/scriptservices/getstream/scene/" + scene_id + "/HLS"
                video_id = scene_id

            else:
                # print("movieid", movie_id)
                # getstream_url = "https://www.nakedsword.com/scriptservices/getstream/movie/" + movie_id + "/DASH"
                getstream_url_m3u8 = "https://www.nakedsword.com/scriptservices/getstream/movie/" + movie_id + "/HLS"
                video_id = movie_id

            # mobj_id= re.match(self._VALID_URL, url)
            # video_id = mobj.group("id")
            # webpage_url = "https://nakedsword.com/movies/" + video_id
            # webpage = self._download_webpage(webpage_url, video_id)

            # getstream_url = "https://www.nakedsword.com/scriptservices/getstream/movie/" + movie_id

            # print("videoid: ", video_id)
            # print("webpage_url: ", webpage_url)
            # print(webpage)

            # print(getstream_url)
            #info = self._download_json(
            #    getstream_url,
            #    video_id,
            #)

            info_m3u8 = self._download_json(
                getstream_url_m3u8,
                video_id,
            )

            #print(info_m3u8)

            #mpd_url = info.get("StreamUrl")

            mpd_url_m3u8 = info_m3u8.get("StreamUrl")

            #formats = self._extract_mpd_formats(
            #    mpd_url, video_id, mpd_id="dash", fatal=False
            #)

            formats_m3u8 = self._extract_m3u8_formats(
                mpd_url_m3u8, video_id, m3u8_id="hls", ext="mp4", entry_protocol='m3u8_native', fatal=False
            )

            #print(formats_m3u8)
            
            n = len(formats_m3u8)
            for f in formats_m3u8:
                f['format_id'] = "hls-" + str(n-1)
                #print(format)
                n = n - 1
            #input("WAIT...")
            #self._sort_formats(formats_m3u8)


            #self._sort_formats(formats)
            title = info_m3u8.get("Title")
            title = sanitize_filename(title)
            title = title.replace(" ", "_")
            if (info_m3u8.get("MediaType") == "Scene"):
                substr = webpage_url.rpartition("/")
                title = title + "_Scene_" + substr[2]

            self._logout()

            return {
                "id": video_id,
                "title": title,
                #"formats": formats + formats_m3u8,
                "formats": formats_m3u8,
                "ext": "mp4"
            }
        except Exception as e:
            print(e)
            self._logout()
            return None
