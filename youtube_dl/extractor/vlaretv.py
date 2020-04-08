# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import urljoin
import re


class VlaretvPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://vlare\.tv/u/(?P<Channel_id>[0-9a-zA-Z]+)/playlist/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://vlare.tv/u/LVWDDFhi/playlist/2568',
        'info_dict': {
            'id': '2568',
            'title': 'LHA',
        },
        'playlist_count': 11,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        urls = re.findall(r'<a href="(.+?)" class="video_thumbnail"', webpage)
        title = self._html_search_regex(r'<title>(.+?) \| Vlare</title>', webpage, 'title')

        # When playlist points to deleted video there is an "error" in the url (Ex. https://vlare.tv/v/error/3257)
        entries = [self.url_result(urljoin('https://vlare.tv', u)) for u in urls if 'error' not in u]

        return self.playlist_result(entries, playlist_id, title)
