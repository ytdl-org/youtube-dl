# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re


class TwitcastingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|ssl|en|pt|es|ja|ko\.)?twitcasting\.tv/(?P<uploader_id>[^\/]+)/movie/(?P<video_id>[0-9]+)'
    _TEST = {
        'url': 'https://twitcasting.tv/ivetesangalo/movie/2357609',
        'md5': '745243cad58c4681dc752490f7540d7f',
        'info_dict': {
            'id': '2357609',
            'ext': 'mp4',
            'title': 'Recorded Live #2357609',
            'uploader_id': 'ivetesangalo',
            'description': "Moi! I'm live on TwitCasting from my iPhone.",
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        uploader_id = mobj.group('uploader_id')

        webpage = self._download_webpage(url, video_id)

        playlist_url = self._html_search_regex(r'(["\'])(?P<url>http.+?\.m3u8.*?)\1', webpage, name='playlist url', group='url')
        formats = self._extract_m3u8_formats(playlist_url.group('url'), video_id, ext='mp4')
        thumbnail = self._og_search_thumbnail(webpage)
        title = self._html_search_meta('twitter:title', webpage)
        description = self._og_search_description(webpage) or self._html_search_meta('twitter:description', webpage)
        return{
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader_id,
            'formats': formats,
        }
