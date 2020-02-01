# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import urlencode_postdata

import re


class TwitCastingIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?twitcasting\.tv/(?P<uploader_id>[^/]+)/movie/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://twitcasting.tv/ivetesangalo/movie/2357609',
        'md5': '745243cad58c4681dc752490f7540d7f',
        'info_dict': {
            'id': '2357609',
            'ext': 'mp4',
            'title': 'Live #2357609',
            'uploader_id': 'ivetesangalo',
            'description': "Moi! I'm live on TwitCasting from my iPhone.",
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://twitcasting.tv/mttbernardini/movie/3689740',
        'info_dict': {
            'id': '3689740',
            'ext': 'mp4',
            'title': 'Live playing something #3689740',
            'uploader_id': 'mttbernardini',
            'description': "I'm live on TwitCasting from my iPad. password: abc (Santa Marinella/Lazio, Italia)",
            'thumbnail': r're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,
            'videopassword': 'abc',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        uploader_id = mobj.group('uploader_id')

        video_password = self._downloader.params.get('videopassword')
        request_data = None
        if video_password:
            request_data = urlencode_postdata({
                'password': video_password,
            })
        webpage = self._download_webpage(url, video_id, data=request_data)

        title = self._html_search_regex(
            r'(?s)<[^>]+id=["\']movietitle[^>]+>(.+?)</',
            webpage, 'title', default=None) or self._html_search_meta(
            'twitter:title', webpage, fatal=True)

        m3u8_url = self._search_regex(
            (r'data-movie-url=(["\'])(?P<url>(?:(?!\1).)+)\1',
             r'(["\'])(?P<url>http.+?\.m3u8.*?)\1'),
            webpage, 'm3u8 url', group='url')

        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='hls')

        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader_id': uploader_id,
            'formats': formats,
        }
