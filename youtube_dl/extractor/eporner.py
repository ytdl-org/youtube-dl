# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    str_to_int,
)


class EpornerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?eporner\.com/hd-porn/(?P<id>\d+)/(?P<display_id>[\w-]+)'
    _TEST = {
        'url': 'http://www.eporner.com/hd-porn/95008/Infamous-Tiffany-Teen-Strip-Tease-Video/',
        'md5': '39d486f046212d8e1b911c52ab4691f8',
        'info_dict': {
            'id': '95008',
            'display_id': 'Infamous-Tiffany-Teen-Strip-Tease-Video',
            'ext': 'mp4',
            'title': 'Infamous Tiffany Teen Strip Tease Video',
            'duration': 1838,
            'view_count': int,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)
        title = self._html_search_regex(
            r'<title>(.*?) - EPORNER', webpage, 'title')

        redirect_code = self._html_search_regex(
            r'<script type="text/javascript" src="/config5/%s/([a-f\d]+)/">' % video_id,
            webpage, 'redirect_code')
        redirect_url = 'http://www.eporner.com/config5/%s/%s' % (video_id, redirect_code)
        player_code = self._download_webpage(
            redirect_url, display_id, note='Downloading player config')

        sources = self._search_regex(
            r'(?s)sources\s*:\s*\[\s*({.+?})\s*\]', player_code, 'sources')

        formats = []
        for video_url, format_id in re.findall(r'file\s*:\s*"([^"]+)",\s*label\s*:\s*"([^"]+)"', sources):
            fmt = {
                'url': video_url,
                'format_id': format_id,
            }
            m = re.search(r'^(\d+)', format_id)
            if m:
                fmt['height'] = int(m.group(1))
            formats.append(fmt)
        self._sort_formats(formats)

        duration = parse_duration(self._html_search_meta('duration', webpage))
        view_count = str_to_int(self._search_regex(
            r'id="cinemaviews">\s*([0-9,]+)\s*<small>views',
            webpage, 'view count', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }
