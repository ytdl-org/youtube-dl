# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class PlaysTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?plays\.tv/video/(?P<id>[0-9a-f]{18})'
    _TEST = {
        'url': 'http://plays.tv/video/56af17f56c95335490/when-you-outplay-the-azir-wall',
        'md5': 'dfeac1198506652b5257a62762cec7bc',
        'info_dict': {
            'id': '56af17f56c95335490',
            'ext': 'mp4',
            'title': 'When you outplay the Azir wall',
            'description': 'Posted by Bjergsen',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        content = self._parse_json(
            self._search_regex(
                r'R\.bindContent\(({.+?})\);', webpage,
                'content'), video_id)['content']
        mpd_url, sources = re.search(
            r'(?s)<video[^>]+data-mpd="([^"]+)"[^>]*>(.+?)</video>',
            content).groups()
        formats = self._extract_mpd_formats(
            self._proto_relative_url(mpd_url), video_id, mpd_id='DASH')
        for format_id, height, format_url in re.findall(r'<source\s+res="((\d+)h?)"\s+src="([^"]+)"', sources):
            formats.append({
                'url': self._proto_relative_url(format_url),
                'format_id': 'http-' + format_id,
                'height': int_or_none(height),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
