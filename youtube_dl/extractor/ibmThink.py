# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE


class IbmThinkPlaylistIE(InfoExtractor):
    IE_DESC = 'IBM Think Playlist'
    IE_NAME = 'IBMThink:playlist'
    _VALID_URL = r'https?://(?:www\.)?ibm\.com/events/think/watch/playlist/(?P<id>[0-9]+)/?'
    _TESTS = [{
        'url': 'https://www.ibm.com/events/think/watch/playlist/468067/',
        'info_dict': {
            'id': '468067',
            'title': 'Think 2020',
            'description': 'Keynotes'
        },
        'playlist_mincount': 5
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        entries = [self.url_result(m, GenericIE.ie_key()) for m in re.findall(r'<a href="(.+?)" class="video-list-item js-video-list-item">', webpage)]
        title = self._html_search_regex(r'<title>.+?\s\|\s.+?\s\|\s(.+?)</title>', webpage, 'title', fatal=False)
        description = self._og_search_description(webpage)
        return self.playlist_result(entries, playlist_id, title, description)
