# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    urlencode_postdata,
    ExtractorError,
)


class PornTrexBaseIE(InfoExtractor):
    _NETRC_MACHINE = 'porntrex'

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            'https://www.porntrex.com/login/', None, 'Downloading login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'username': username,
            'pass': password,
            'remember_me': 1,
        })

        login_page = self._download_webpage(
            'https://www.porntrex.com/ajax-login/', None,
            note='Logging in',
            data=urlencode_postdata(login_form))

        if re.search(r'generic-error hidden', login_page):
            raise ExtractorError(
                'Unable to login, incorrect username and/or password',
                expected=True)

    def _real_initialize(self):
        self._login()


class PornTrexIE(PornTrexBaseIE):
    _VALID_URL = r'https?://(?:www\.)?porntrex\.com/video/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'https://www.porntrex.com/video/311136/naomi-gets-fingered-before-the-fucking',
        'info_dict': {
            'id': '311136',
            'ext': 'mp4',
            'title': 'Naomi gets fingered before the fucking',
            'uploader': 'cumberland',
            'description': 'Sexy brunette babe likes to get her tight cunt slammed in hardcore fashion.',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # print(self._html_search_meta('description', webpage, 'description', fatal=False))
        # print(self._og_search_description(webpage))
        # quit()

        if re.findall(r'Only active members can watch private videos.', webpage):
            self.raise_login_required()

        title = self._html_search_regex(r'<title>(.+?)</title>',
                                        webpage,
                                        'title',
                                        fatal=False)

        uploader = self._search_regex(r'(?m)/members/\d+?/["\']>\s+(.+?)\s+</a>',
                                      webpage,
                                      'new_uploader',
                                      fatal=False).strip()

        thumbnails_list = re.findall(r'href="(http.*?/screenshots/\d+.jpg/)["\']', webpage)
        thumbnails = []
        for thumbs in thumbnails_list:
            thumbnails.append({'url': thumbs})

        formats = []
        movie_urls = re.findall(r"['\"](https://www.porntrex.com/get_file/.*?)/['\"]", webpage)
        for movie_url in movie_urls:
            formats.append({'url': movie_url,
                            'height': int(self._search_regex(r'_(\d+)p\.',
                                                             movie_url,
                                                             'height',
                                                             default='480')),
                            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': uploader,
            'thumbnails': thumbnails,
            'formats': formats,
            'age_limit': 18,
        }


class PornTrexPlayListIE(PornTrexBaseIE):
    _VALID_URL = r'https?://(?:www\.)?porntrex\.com/playlists/(?P<id>[0-9]+)/'
    _TESTS = [{
        'url': 'https://www.porntrex.com/playlists/13598/tushy32/',
        'info_dict': {
            'id': '13598',
            'title': 'Tushy',
            'description': 'Huge collection of free hd porn videos. Tons of amateur sex and professional hd movies. Daily updated videos of hot busty teen, latina, amateur & more...',
        },
        'playlist_mincount': 74,
    }, {
        'url': 'https://www.porntrex.com/playlists/31075/2016-collection/',
        'info_dict': {
            'id': '31075',
            'title': 'FTVGirls 2016 Collection',
            'description': 'FTVGirls 2016  Complete Collection (122 videos)',
        },
        'playlist_mincount': 3,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        all_urls = re.findall(r'data-playlist-item="(.*?)"', webpage)

        entries = []
        for this_url in all_urls:
            entries.append(self.url_result(this_url))

        playlist_description = self._html_search_meta('description', webpage, 'description', fatal=False)

        playlist_title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title', fatal=False)

        return self.playlist_result(entries,
                                    playlist_id=playlist_id,
                                    playlist_title=playlist_title,
                                    playlist_description=playlist_description)
