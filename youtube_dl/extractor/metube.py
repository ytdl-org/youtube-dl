# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class MetubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?metube\.id/videos/(?P<id>\d+)/(?P<slug>[^/?#&]+)'
    _TEST = {
        'url': 'https://www.metube.id/videos/15090866/dragon-ball-super-eps-131',
        'info_dict': {
            'id': '15090866',
            'slug': 'dragon-ball-super-eps-131',
            'ext': 'm3u8',
            'title': 'Dragon Ball Super Eps.131',
            'description': 'md5:dc4bfa9274e3db15392bfce045964331',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, slug = mobj.group('id', 'slug')

        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_property('image', webpage)
        m3u8_url = self._html_search_regex(
            r'''jwplayer\s*\(\s*["'][^'"]+["']\s*\)\s*\.setup.*?['"]?file['"]?\s*:\s*["\'](.*?)["\']''',
            webpage, 'm3u8_url', default='{}', fatal=False)
        formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'm3u8', entry_protocol='m3u8_native')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'slug': slug,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats
        }
