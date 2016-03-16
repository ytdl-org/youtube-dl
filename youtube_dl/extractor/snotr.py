# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    str_to_int,
    parse_duration,
)


class SnotrIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?snotr\.com/video/(?P<id>\d+)/([\w]+)'
    _TESTS = [{
        'url': 'http://www.snotr.com/video/13708/Drone_flying_through_fireworks',
        'info_dict': {
            'id': '13708',
            'ext': 'flv',
            'title': 'Drone flying through fireworks!',
            'duration': 247,
            'filesize_approx': 98566144,
            'description': 'A drone flying through Fourth of July Fireworks',
        }
    }, {
        'url': 'http://www.snotr.com/video/530/David_Letteman_-_George_W_Bush_Top_10',
        'info_dict': {
            'id': '530',
            'ext': 'flv',
            'title': 'David Letteman - George W. Bush Top 10',
            'duration': 126,
            'filesize_approx': 8912896,
            'description': 'The top 10 George W. Bush moments, brought to you by David Letterman!',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)

        description = self._og_search_description(webpage)
        video_url = 'http://cdn.videos.snotr.com/%s.flv' % video_id

        view_count = str_to_int(self._html_search_regex(
            r'<p>\n<strong>Views:</strong>\n([\d,\.]+)</p>',
            webpage, 'view count', fatal=False))

        duration = parse_duration(self._html_search_regex(
            r'<p>\n<strong>Length:</strong>\n\s*([0-9:]+).*?</p>',
            webpage, 'duration', fatal=False))

        filesize_approx = float_or_none(self._html_search_regex(
            r'<p>\n<strong>Filesize:</strong>\n\s*([0-9.]+)\s*megabyte</p>',
            webpage, 'filesize', fatal=False), invscale=1024 * 1024)

        return {
            'id': video_id,
            'description': description,
            'title': title,
            'url': video_url,
            'view_count': view_count,
            'duration': duration,
            'filesize_approx': filesize_approx,
        }
