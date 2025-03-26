# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

import re
import json

class NoodleDudeIE(InfoExtractor):
    IE_NAME = 'NoodleDude'
    _VALID_URL = r'https?://(www\.)?noodledude\.io/videos/(?P<id>[0-9a-zA-Z_-]+)'
    _TEST = {
        'url': 'https://www.noodledude.io/videos/kawaii-vs-goth',
        'md5': '9d3465ea49d16860a531035517ea8aec',
        'info_dict': {
            'id': 'kawaii-vs-goth',
            'ext': 'mp4',
            'title': 'Kawaii VS Goth',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'md5:f16fef1f758a4dc38041bd6648b9d3b2',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers={'Referer': 'https://www.noodledude.io/'})

        #with open('webpage.tmp', 'w') as f:
            #f.write(webpage)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1 id="video-title".*?>(.+?)</h1>', webpage, 'title')
        description = self._html_search_meta('description', webpage, 'decription')

        print('Title:', title)
        print('Description:', description)

        iframe_url = self._search_regex(r'<iframe\s*src="(.+?)"', webpage, 'iframe_url', flags=re.MULTILINE)
        #print('iframe: ', iframe_url)

        iframe_data = self._download_webpage(iframe_url, video_id, headers={'Referer': 'https://www.noodledude.io/'}) 
        #with open('iframe.tmp', 'w') as f:
            #f.write(iframe_data)

        m3u8_url = self._search_regex(r'<source.*?src="(.+?)"', iframe_data, 'm3u8_url')
        print('M3U8:', m3u8_url)

        poster_url = self._search_regex(r'<video.*?data-poster="(.+?)"', iframe_data, 'poster_url')
        print('Poster:', poster_url)

        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', headers={'Referer': 'https://iframe.mediadelivery.net/'})
        print('Formats:', json.dumps(formats))
        for f in formats:
            f.setdefault('http_headers', {})['Referer'] = 'https://iframe.mediadelivery.net/'

        return {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'formats': formats,
            'thumbnail': poster_url
            #'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
