# coding: utf-8
from __future__ import unicode_literals

import re
import json


from .common import InfoExtractor

import requests 


from ..utils import (
    ExtractorError,
    urlencode_postdata,
    urljoin,
    int_or_none,
    sanitize_filename

)


class BoyFriendTVBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.boyfriendtv.com/login'
    _SITE_URL = 'https://www.boyfriendtv.com'
    _NETRC_MACHINE = 'boyfriendtv'
    _LOGOUT_URL = 'https://www.boyfriendtv.com/logout'
    _PROFILE_URL = 'https://www.boyfriendtv.com/profiles/1778026/'
    
    def is_logged(self, url):
        return (url == self._SITE_URL + "/")
    
    def _login(self):
        self.username, self.password = self._get_login_info()
        if self.username is None:
            return

        login_page, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Downloading login page')

        
        if self.is_logged(urlh.geturl()):
            return

        login_form = self._form_hidden_inputs('loginForm', login_page)

        login_form.update({
            "login": self.username,
            "password": self.password
        })

        post_url = urljoin(self._LOGIN_URL, self._search_regex(
            r'<form[^>]+action=(["\'])(?P<url>.+?)\1', login_page,
            'post url', default=self._LOGIN_URL, group='url'))
        
        if not post_url.startswith('http'):
            post_url = urljoin(self._LOGIN_URL, post_url)
        

        response, urlh = self._download_webpage_handle(
            post_url, None, 'Logging in', 'Wrong login info',
            data=urlencode_postdata(login_form),
            headers={'Content-Type': 'application/x-www-form-urlencoded'})

      
        # Successful login
        if self.is_logged(urlh.geturl()):
            return

        else:
            raise ExtractorError('Unable to log in', expected=True)

    def _logout(self):
        login_page, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'logout page',
            headers={'Referer': self._PROFILE_URL})
        
        if urlh == self._SITE_URL:
            return
        else:
            raise ExtractorError('Unable to log out', expected=True)

 
class BoyFriendTVIE(BoyFriendTVBaseIE):
    IE_NAME = 'boyfriendtv'
    _VALID_URL = r'https?://(?:(?P<prefix>m|www|es|ru|de)\.)?(?P<url>boyfriendtv\.com/videos/(?P<video_id>[0-9]+)/?(?:([0-9a-zA-z_-]+/?)|$))'
    _SOURCES_FORM = r'sources: {(?P<type>.+?):\[(?P<sources>.+?)\]}'

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')

        
        webpage, urlh = self._download_webpage_handle(
            url, video_id, "Downloading web page video",
            headers={'X-Requested-With': 'XMLHttpRequest'})

        if not 'VideoPlayer' in webpage:
            webpage, urlh = self._download_webpage_handle(
                self._LOGIN_URL + "/?fw=" + url, video_id, "login web page video",
                headers={'X-Requested-With': 'XMLHttpRequest'})
            
            login_form = self._form_hidden_inputs('loginForm', webpage)

            login_form.update({
                "login": self.username,
                "password": self.password
            })

            post_url = urljoin(self._LOGIN_URL, self._search_regex(
                r'<form[^>]+action=(["\'])(?P<url>.+?)\1', webpage,
                'post url', default=self._LOGIN_URL, group='url'))
            
            if not post_url.startswith('http'):
                post_url = urljoin(self._LOGIN_URL, post_url)
            

            response, urlh = self._download_webpage_handle(
                post_url, None, 'Logging in', 'Wrong login info',
                data=urlencode_postdata(login_form),
                headers={'Content-Type': 'application/x-www-form-urlencoded'})

            webpage, urlh = self._download_webpage_handle(url, video_id, "Downloading web page video",
                                            headers={'X-Requested-With': 'XMLHttpRequest'})


        
        sources = self._search_regex(self._SOURCES_FORM, webpage, 'sources', default=None, group='sources', fatal=False)
        if sources:
            sources = "[" + sources + "]"
        else:
            raise ExtractorError("No video info", expected=True)  
            

        video_title = self._search_regex(r'title: "(?P<title>.+?)"', webpage, 'title', group='title')    
        
        video_type = re.search(self._SOURCES_FORM, webpage).group('type')
        
        sources_json = json.loads(sources)
        
        formats = []

        for src in sources_json:
            url_v = src['src'].replace("\\","")
            filesize = None
            try:
                #res = requests.get(url_v, stream=True)
                res = requests.head(url_v)
                filesize = int(res.headers['Content-Length'])
                #filesize = int(requests.head(url_v).headers['content-length'])
            except Exception as e:
                pass

            formats.append({
                'format_id': "mp4",
                'url': url_v,
                'height': int(src['desc'][:-1]),
                'filesize': filesize
            })

        self._sort_formats(formats)

        average_rating = int_or_none(self._search_regex(
            r'<div class="progress-big js-rating-title" title="(?P<average_rating>.+?)%">', webpage, 'average_rating', group='average_rating'))


        return ({
            'id': video_id,
            'title': sanitize_filename(video_title, True),
            'formats': formats,
            'average_rating': average_rating
        })


class BoyFriendTVPlayListIE(BoyFriendTVBaseIE):
    IE_NAME = 'boyfriendtvplaylist'
    IE_DESC = 'boyfriendtvplaylist'
    _VALID_URL = r'https?://(?:(m|www|es|ru|de)\.)boyfriendtv\.com/playlists/(?P<playlist_id>.*?)(?:(/|$))'

    def _real_initialize(self):
        self._login()
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('playlist_id')


        webpage = self._download_webpage(url, playlist_id, "Downloading web page playlist")

        pl_title = self._html_search_regex(r'(?s)<h1>(?P<title>.*?)<', webpage, 'title', group='title')
        
        entries = []

        i = 2
        ep_id = 0
        while True:

            if webpage:            
                videos_paths = re.findall(
                    r'(?s)<li class="playlist-video-thumb thumb-item videospot">.*?<a href="([^"]+)"',
                    webpage)
                titles_list = re.findall(
                    r'(?s)<li class="playlist-video-thumb thumb-item videospot">.*?title="([^"]+)"',
                    webpage)
                rating_list = re.findall(
                    r'(?s)<div class="progress-small js-rating-title.*?title="([^"]+)%"',
                    webpage)
                ids_list = re.findall(
                    r'(?s)<li class="playlist-video-thumb thumb-item videospot">.*?data-video-id="([^"]+)"',
                    webpage)

                lista_len = [len(videos_paths), len(titles_list), len(rating_list), len(ids_list)]
                if len(set(lista_len)) > 1:
                    raise ExtractorError("Data mismatch for videos in the playlist")                   
                
                for j, video in enumerate(videos_paths):
                    
                    entry = self.url_result(self._SITE_URL + video.split("?pl")[0], 'BoyFriendTV', ids_list[j], sanitize_filename(titles_list[j], True)) 
                    entry.update({'average_rating': rating_list[j]}) 
                    entries.append(entry)
                    ep_id += 1
              

                if '<link rel="next"' in webpage:

                    webpage = self._download_webpage(urljoin(url+"/*",str(i)), playlist_id, f"Downloading web page playlist {i}")
                    i += 1

                else:
                    break
            else:
                break

                

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': sanitize_filename(pl_title, True),
            'entries': entries,
        }