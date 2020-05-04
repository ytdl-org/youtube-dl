# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ServusIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            servus\.com/(?:(?:at|de)/p/[^/]+|tv/videos)|
                            servustv\.com/videos
                        )
                        /(?P<id>[aA]{2}-\w+|\d+-\d+)
                    '''
    _TESTS = [{
        # new URL schema
        'url': 'https://www.servustv.com/videos/aa-1t6vbu5pw1w12/',
        'md5': '3e1dd16775aa8d5cbef23628cfffc1f4',
        'info_dict': {
            'id': 'AA-1T6VBU5PW1W12',
            'ext': 'mp4',
            'title': 'Die Grünen aus Sicht des Volkes',
            'description': 'md5:1247204d85783afe3682644398ff2ec4',
            'thumbnail': r're:^https?://.*\.jpg',
        }
    }, {
        # old URL schema
        'url': 'https://www.servus.com/de/p/Die-Gr%C3%BCnen-aus-Sicht-des-Volkes/AA-1T6VBU5PW1W12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/at/p/Wie-das-Leben-beginnt/1309984137314-381415152/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/aa-1t6vbu5pw1w12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/1380889096408-1235196658/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).upper()
        webpage = self._download_webpage(url, video_id)

        title = self._search_regex(
            (r'videoLabel\s*=\s*(["\'])(?P<title>(?:(?!\1).)+)\1',
             r'<h\d+[^>]+\bclass=["\']heading--(?:one|two)["\'][^>]*>(?P<title>[^<]+)'),
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)
        title = re.sub(r'\s*-\s*Servus TV\s*$', '', title)
        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        formats = self._extract_m3u8_formats(
            'https://stv.rbmbtnx.net/api/v1/manifests/%s.m3u8' % video_id,
            video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
