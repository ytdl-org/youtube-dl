# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    merge_dicts
)


class PlayvidsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?playvids(?:\.com/.*v/|\.com/)(?P<id>[\_\-0-9a-zA-Z]{5,20})(?:$|[#\?/])'
    _TESTS = [{
        'url': 'https://www.playvids.com/v/47iUho33toY',
        'md5': '4365a9a3dd0e82d64a50fe0d5349b0b3',
        'info_dict': {
            'id': '47iUho33toY',
            'ext': 'm3u8',
            'title': 'KATEE OWEN STRIPTIASE IN SEXY RED LINGERIE, Cacerenele',
            'age_limit': 18,
            'upload_date': '20171003',
            'description': 'Watch KATEE OWEN STRIPTIASE IN SEXY RED LINGERIE video in HD, uploaded by Cacerenele',
            'timestamp': 1507052209,
        }
    }, {
        'url': 'https://www.playvids.com/z3_7iwWCmqt/sexy-teen-filipina-striptease-beautiful-pinay-bargirl-strips-and-dances',
        'md5': '1997acf4862575fadf32f1997afc0d9c',
        'info_dict': {
            'id': 'z3_7iwWCmqt',
            'ext': 'm3u8',
            'title': 'SEXY TEEN FILIPINA STRIPTEASE - Beautiful Pinay Bargirl Strips and Dances, yorours',
            'age_limit': 18,
            'upload_date': '20201208',
            'description': 'Watch SEXY TEEN FILIPINA STRIPTEASE - Beautiful Pinay Bargirl Strips and Dances video, uploaded by yorours',
            'timestamp': 1607470323,

        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title', fatal=False).strip()
        video_tags = re.findall(r'(data-dash-src|data-hls-src[0-9]*?)="([^"]*)"', webpage)
        json_ld_data = self._search_json_ld(webpage, video_id, default={})
        formats = []

        for n in video_tags:
            height = re.findall(r'hls-src([\d]+)', n[0])
            if height:
                formats.append({
                    'url': n[1].replace("&amp;", "&"),
                    'format_id': 'hls-%sp' % height[0],
                    'height': int_or_none(height[0]),
                })
            elif n[0] == 'data-dash-src':
                formats.extend(self._extract_mpd_formats(n[1].replace("&amp;", "&"), video_id, mpd_id='dash', fatal=False))

        self._sort_formats(formats)

        return merge_dicts(json_ld_data, {
            'id': video_id,
            'title': title,
            'formats': formats,
            'age_limit': 18,
        })
