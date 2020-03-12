# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class VlaretvIE(InfoExtractor):
    _VALID_URL = r'https?:\/\/vlare.tv\/v\/(?P<id>[0-9a-zA-Z]+)'
    IE_NAME = 'vlare.tv'
    _TESTS = [
        {
            'url': 'https://vlare.tv/v/cTQKAh0z',
            'info_dict': {
                'id': 'cTQKAh0z',
                'ext': 'mp4',
                'title': 'Interspecies Reviewers Abridged | One Shot (Parody)',
            }
        },
        {
            'url': 'https://vlare.tv/v/HSzfUoye',
            'info_dict': {
                'id': 'HSzfUoye',
                'ext': 'mp4',
                'title': 'Quake II (1997) - Gameplay AMD K6-III+ and 3dfx Voodoo Banshee',
            }
        },
        {
            'url': 'https://vlare.tv/v/t7XSuZfK/2568',
            'info_dict': {
                'id': 'HSzfUoye',
                'ext': 'mp4',
                'title': 'Quake II (1997) - Gameplay AMD K6-III+ and 3dfx Voodoo Banshee',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)<\/title>', webpage, 'title').replace(' | Vlare', '')
        video_urls = self._html_search_regex(r'sources: \[{"file":(.+?)\],', webpage, 'video_urls')
        video_urls = video_urls.split(',')
        video_urls_clean = []
        for i in video_urls:
            if 'http' in i:
                video_urls_clean.insert(0, {'url': i.replace("\"", "").replace("\n", "").replace("{file:", "")})
        return {
            'id': video_id,
            'title': title,
            'formats': video_urls_clean
        }


class VlaretvPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://vlare.tv/u/(?P<Channel_id>[0-9a-zA-Z]+)/playlist/(?P<id>[0-9]+)'
    IE_NAME = 'Vlare.tv Playlist'
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
        title = self._html_search_regex(r'<title>(.+?)<\/title>', webpage, 'title').split('|')[1][1:-1]
        entries = []
        for i in urls:
            entry = {
                '_type': 'url_transparent',
                'url': 'https://vlare.tv' + i,
                'id': re.match(r'\/v\/(.+?)\/', i),
            }
            entries.append(entry)

        return {
            '_type': 'playlist',
            'title': title,
            'id': self._match_id(url),
            'entries': entries,
        }
