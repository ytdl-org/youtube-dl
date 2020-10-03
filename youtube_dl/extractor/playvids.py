# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class PlayvidsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?playvids\.com/(?P<id>.+?)/(?P<seo>.+?)(?:$|[#\?])'
    _TEST = {
        'url': 'https://www.playvids.com/bKmGLe3IwjZ/sv/brazzers-800-phone-sex-madison-ivy-always-on-the-line',
        'md5': '3b57615c81d5580919d3a0b216056a15',
        'info_dict': {
            'id': 'bKmGLe3IwjZ',
            'ext': 'mp4',
            'title': 'Brazzers - 1 800 Phone Sex: Madison Ivy Always On The Line 6',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title').strip()

        # search for the video urls
        video_tags = re.findall(r'data-hls-src[0-9]*?="https:\/\/.*?userscontent.net.*?\.mp4\/index.m3u8\?seclink=.*?sectime=[0-9]*"', webpage)

        # get the url from each match
        video_urls = []
        for n in video_tags:
            video_urls.append(self._html_search_regex(r'"(.*?)"', n, 'url').replace("&amp;", "&"))

        # reverse list so the best format is first
        video_urls.reverse()

        # check if nothing was found before attempting anything
        if len(video_urls) == 0:
            raise ExtractorError('No video URLs found')
        else:
            return {
                'id': video_id,
                'title': title,
                'url': video_urls[0],
                'ext': 'mp4',
                'age_limit': 18,
            }
