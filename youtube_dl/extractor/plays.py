# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none


class PlaysTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?plays\.tv/video/(?P<id>[0-9a-f]{18})'
    _TESTS = [{
        'url': 'https://plays.tv/video/57698d69e6c84884a2/just-a-typical-reaper-potg',
        'md5': 'c4bdc35a0c9ca1f95c6ecad2f99c0e76',
        'info_dict': {
            'id': '57698d69e6c84884a2',
            'ext': 'mp4',
            'title': 'Solfect - Just a typical Reaper POTG',
            'description': 'Posted by Solfect',
        }
    }, {
        'url': 'https://plays.tv/video/56af17f56c95335490/when-you-outplay-the-azir-wall',
        'md5': 'dfeac1198506652b5257a62762cec7bc',
        'info_dict': {
            'id': '56af17f56c95335490',
            'ext': 'mp4',
            'title': 'Bjergsen - When you outplay the Azir wall',
            'description': 'Posted by Bjergsen',
        }
    }, {
        'url': 'https://plays.tv/video/58236095d388d140aa/-?from=user',
        'md5': '09535d1d157f679e6446fb39ce51645a',
        'info_dict': {
            'id': '58236095d388d140aa',
            'ext': 'mp4',
            'title': 'akn3ex - \u63a7\u3048\u3081\u306b\u8a00\u3063\u3066\u9811\u5f35\u3063\u3066\u308b',
            'description': 'Posted by akn3ex',
        }
    }, {
        'url': 'http://plays.tv/video/56d77f74866aa25854/pro-abortion-propaganda?from=search&search=dota+2',
        'md5': '3e3fc1d5c20cb373eb3143bbb4ca5070',
        'info_dict': {
            'id': '56d77f74866aa25854',
            'ext': 'mp4',
            'title': 'SavageIs - pro abortion propaganda',
            'description': 'Posted by SavageIs',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        content = self._search_regex(
            r'<script class=\"linked_data\" type=\"application\/ld\+json\">{(.+?)}<\/script>', webpage, 'content')
        content = self._parse_json("{" + content + "}", video_id)
        title = content['name']
        mpd_url, sources = re.search(
            r'(?s)<video[^>]+data-mpd="([^"]+)"[^>]*>(.+?)</video>',
            webpage).groups()
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
