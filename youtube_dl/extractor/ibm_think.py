# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .generic import GenericIE


class IbmThinkIE(InfoExtractor):
    IE_DESC = 'IBM Think Videos'
    IE_NAME = 'IBMThink'
    _VALID_URL = r'https?://(?:www\.)?ibm\.com/events/think/watch/(playlist/)?(\d*/)?replay/(?P<id>[0-9]+)/?'
    _TESTS = [{
        'url': 'https://www.ibm.com/events/think/watch/replay/113734399/',
        'md5': '0a3f1c81c58aacbbb36e292a1c1f9690',
        'info_dict': {
            'id': '113734399',
            'ext': 'mp4',
            'title': 'Think 2018 Chairman\'s Address: Putting Smart to Work',
            'timestamp': 1521575552,
            'upload_date': '20180320',
            'uploader': 'f8k4md3yana',
            'uploader_id': '43178333',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        ustream_url = self._html_search_regex(r'<iframe\ssrc="(.*?)"', webpage, 'ustream_url').split('?')[0] + '/'
        return self.url_result(ustream_url, GenericIE.ie_key())


class IbmThinkPlaylistIE(InfoExtractor):
    IE_DESC = 'IBM Think Playlist'
    IE_NAME = 'IBMThink:playlist'
    _VALID_URL = r'https?://(?:www\.)?ibm\.com/events/think/watch/playlist/(?P<id>[0-9]+)/?'
    _TESTS = [{
        'url': 'https://www.ibm.com/events/think/watch/playlist/241295/',
        'info_dict': {
            'id': '241295',
            'title': 'Five innovations that will help change our lives within five years',
            'description': 'Discover what the world is thinking at Think 2018, IBM\'s first business event to go beyond IT conference, exploring cloud technology, data analytics & security.'
        },
        'playlist_mincount': 6
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        entries = [self.url_result(m, GenericIE.ie_key()) for m in re.findall(r'<a href="(.+?)" class="video-list-item js-video-list-item?">', webpage)]
        title = self._html_search_regex(r'<title>.+?\s\|\s.+?\s\|\s(.+?)</title>', webpage, 'title', fatal=False)
        description = self._og_search_description(webpage)
        return self.playlist_result(entries, playlist_id, title, description)
