# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class VidozaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidoza\.net/(?P<id>[0-9]+).html'
    _TEST = {
        'url': 'https://vidoza.net/4u4xijoms5si.html',
        'info_dict': {
            'id': '4u4xijoms5si',
            'ext': 'mp4',
            'title': 'Watch video 2019 mp4'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = re.search(r'<title>(.+?)\n</title>', webpage).group(1)
        video_link = re.search(r'sourcesCode: [{ src: "(.+?)",', webpage).group(1)

        return {
            'id': video_id,
            'title': title,
            'url': video_link
        }
