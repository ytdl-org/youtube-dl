# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re


class PornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?porn\.com/videos/.+'
    _TEST = {

        'url': 'http://www.porn.com/videos/marsha-may-rides-seth-on-top-of-his-thick-cock-2658067',
        'info_dict': {
            'id': '2658067',
            'ext': 'mp4',
            'title': 'Marsha May rides Seth on top of his thick cock',
            }
    }

    def _real_extract(self, url):
        video_id = self._search_regex(r'(?:\w-)+(\d+)', url, 'video_id')
        webpage = self._download_webpage(url, video_id)

        video_urls = re.findall('"([^"]*(?=mp4).*?)"', webpage)
        title = self._search_regex(r'title:"([^title"].*?)"', webpage, 'video_title')

        formats = []
        for vid in video_urls:

            match = re.match('.*_(\d{3})\.mp4.*', vid)
            if match:
                resolution = match.group(1) + 'p'
            else:
                resolution = ""

            a_format = {
                    'id': video_id,
                    'url': vid,
                    'resolution': resolution,
                    }
            formats.append(a_format)

        return {
            'id': video_id,
            'title': title,
            'formats': formats
         }
