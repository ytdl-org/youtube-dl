# coding: utf-8
from __future__ import unicode_literals

import base64

from .common import InfoExtractor


class DumpertIE(InfoExtractor):
    _VALID_URL = (r'https?://(?:www\.)?dumpert\.nl/mediabase/'
                  r'(?P<id>[0-9]+/[0-9a-zA-Z]+)/?.*')
    _TEST = {
        'url': 'http://www.dumpert.nl/mediabase/6646981/951bc60f/',
        'md5': '1b9318d7d5054e7dcb9dc7654f21d643',
        'info_dict': {
            'id': '6646981/951bc60f',
            'ext': 'mp4',
            'title': 'Ik heb nieuws voor je',
            'description': 'Niet schrikken hoor'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('title', webpage)
        description = self._html_search_meta('description', webpage)

        files_base64 = self._html_search_regex(r'data-files="(.*?)"',
                                               webpage,
                                               'files')
        files_json = base64.b64decode(files_base64).decode('iso-8859-1')
        files = self._parse_json(files_json, video_id)

        format_names = ['flv', 'mobile', 'tablet', '720p']
        formats = [{'format_id': name,
                    'url': files[name].replace(r'\/', '/')}
                   for name in format_names
                   if name in files]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats
        }
