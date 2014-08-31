# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    str_to_int,
)


class EpornerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eporner\.com/hd-porn/(?P<id>\d+)/(?P<title_dash>[\w-]+)/?'
    _TEST = {
        'url': 'http://www.eporner.com/hd-porn/95008/Infamous-Tiffany-Teen-Strip-Tease-Video/',
        'md5': '3b427ae4b9d60619106de3185c2987cd',
        'info_dict': {
            'id': '95008',
            'ext': 'flv',
            'title': 'Infamous Tiffany Teen Strip Tease Video',
            'duration': 194,
            'view_count': int,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(
            r'<title>(.*?) - EPORNER', webpage, 'title')

        redirect_code = self._html_search_regex(
            r'<script type="text/javascript" src="/config5/%s/([a-f\d]+)/">' % video_id,
            webpage, 'redirect_code')
        redirect_url = 'http://www.eporner.com/config5/%s/%s' % (video_id, redirect_code)
        webpage2 = self._download_webpage(redirect_url, video_id)
        video_url = self._html_search_regex(
            r'file: "(.*?)",', webpage2, 'video_url')

        duration = parse_duration(self._search_regex(
            r'class="mbtim">([0-9:]+)</div>', webpage, 'duration',
            fatal=False))
        view_count = str_to_int(self._search_regex(
            r'id="cinemaviews">\s*([0-9,]+)\s*<small>views',
            webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'duration': duration,
            'view_count': view_count,
        }
