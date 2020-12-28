# coding: utf-8
from __future__ import unicode_literals

from .vimeo import VHXEmbedIE

from ..utils import ExtractorError

import re


class DropoutIE(VHXEmbedIE):
    IE_NAME = 'dropout'
    IE_DESC = 'Dropout.tv'
    _NETRC_MACHINE = 'dropouttv'
    _LOGIN_URL = 'https://www.dropout.tv/login'
    _LOGOUT_URL = 'https://www.dropout.tv/logout'
    _VALID_URL = r'https://www\.dropout\.tv/(?:[^/]+/(?:season:[^/]/)?)?videos/(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://www.dropout.tv/dimension-20-tiny-heist/season:1/videos/big-little-crimes',
            'md5': '46edf4c6d632e2771a42a235f920b8f7',
            'info_dict': {
                'id': '382486557',
                'ext': 'mp4',
                'uploader': 'OTT Videos',
                'uploader_id': 'user80538407',
                'title': "Untitled",
                'thumbnail': r're:^https://i.vimeocdn.com/.*\.jpg$',
            }
        },
        {
            'url': 'https://www.dropout.tv/videos/um-actually-behind-the-scenes',
            'md5': '7fd342c652a86b996bae2920695593af',
            'info_dict': {
                'id': '265656116',
                'ext': 'mp4',
                'uploader': 'OTT Videos',
                'uploader_id': 'user80538407',
                'title': 'Um, Actually: Behind the Scenes',
                'thumbnail': r're:^https://i.vimeocdn.com/.*\.jpg$',
            }
        }
    ]

    def _real_initialize(self):
        self._login()

    def _login(self):
        email, password = self._get_login_info()
        if (email is None or password is None) and self._downloader.params.get('cookiefile') is None:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
        self._vhx_login(email, password, self._LOGIN_URL)

    def _real_extract(self, url):
        webpage = self._download_webpage(url, None)
        if "The device limit for your account has been reached" in webpage:
            raise ExtractorError('Device Limit reached', expected=True)
        if "Start your free trial" in webpage or "Start Free Trial" in webpage or "Sign in" in webpage:
            raise ExtractorError('You don\'t seem to be logged in', expected=True)

        video = self._html_search_regex(r'<iframe[^>]*"(?P<embed>https://embed.vhx.tv/videos/[0-9]+[^"]*)"[^>]*>', webpage, 'embed')
        video_id = self._search_regex(r'https://embed.vhx.tv/videos/(?P<id>[0-9]+)', video, 'id')
        video_title = self._html_search_regex(r'<h1 class="[^"]*video-title[^"]*"[^>]*>\s*<strong>(?P<title>[^<]+)<', webpage, 'title', fatal=False)
        return self.url_result(video, video_id=video_id, video_title=video_title)


class DropoutPlaylistIE(DropoutIE):
    IE_NAME = 'dropout:playlist'
    _VALID_URL = r'https://www\.dropout\.tv/(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://www.dropout.tv/um-actually',
            'md5': 'ebcd26ef54f546225e7cb96e79da31cc',
            'playlist_count': 33,
            'info_dict': {
                'id': 'um-actually',
                'title': 'Um, Actually',
            }
        },
        {
            'url': 'https://www.dropout.tv/new-releases',
            'md5': 'ebcd26ef54f546225e7cb96e79da31cc',
            'playlist_count': 15,
            'info_dict': {
                'id': 'new-releases',
                'title': 'New Releases',
            }
        },
        {
            'url': 'https://www.dropout.tv/troopers-the-web-series/season:2',
            'md5': 'ebcd26ef54f546225e7cb96e79da31cc',
            'playlist_count': 10,
            'info_dict': {
                'id': 'troopers-the-web-series/season:2',
                'title': 'Troopers: The Web Series',
            }
        }
    ]

    @classmethod
    def suitable(cls, url):
        return False if DropoutIE.suitable(url) else super(DropoutPlaylistIE, cls).suitable(url)

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        playlist_title = self._html_search_regex(r'<h1 class="[^"]*collection-title[^"]*"[^>]*>(?P<title>[^<]+)<', webpage, 'title')    

        items = []
        while True:
            items.extend(re.findall(r'browse-item-title[^>]+>[^<]*<a href="(?P<url>https://www.dropout.tv/[^/]+/[^"]+)"', webpage))
            next_page_url = self._search_regex(r'href="([^"]+\?[^"]*(?:&|&amp;)?page=\d+)"', webpage, 'next page url', default=None)
            if not next_page_url:
                break
            webpage = self._download_webpage('https://www.dropout.tv' + next_page_url, playlist_id)

        return self.playlist_from_matches(items, playlist_id=playlist_id, playlist_title=playlist_title)
