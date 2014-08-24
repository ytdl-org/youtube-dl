from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class ExpoTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.expotv\.com/videos/[^?#]*/(?P<id>[0-9]+)($|[?#])'
    _TEST = {
        'url': 'http://www.expotv.com/videos/reviews/1/24/LinneCardscom/17561',
        'md5': '2985e6d7a392b2f7a05e0ca350fe41d0',
        'info_dict': {
            'id': '17561',
            'ext': 'mp4',
            'upload_date': '20060212',
            'title': 'My Favorite Online Scrapbook Store',
            'view_count': int,
            'description': 'You\'ll find most everything you need at this virtual store front.',
            'uploader': 'Anna T.',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        player_key = self._search_regex(
            r'<param name="playerKey" value="([^"]+)"', webpage, 'player key')
        config_url = 'http://client.expotv.com/video/config/%s/%s' % (
            video_id, player_key)
        config = self._download_json(
            config_url, video_id,
            note='Downloading video configuration')

        formats = [{
            'url': fcfg['file'],
            'height': int_or_none(fcfg.get('height')),
            'format_note': fcfg.get('label'),
            'ext': self._search_regex(
                r'filename=.*\.([a-z0-9_A-Z]+)&', fcfg['file'],
                'file extension', default=None),
        } for fcfg in config['sources']]
        self._sort_formats(formats)

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = config.get('image')
        view_count = int_or_none(self._search_regex(
            r'<h5>Plays: ([0-9]+)</h5>', webpage, 'view counts'))
        uploader = self._search_regex(
            r'<div class="reviewer">\s*<img alt="([^"]+)"', webpage, 'uploader',
            fatal=False)
        upload_date = unified_strdate(self._search_regex(
            r'<h5>Reviewed on ([0-9/.]+)</h5>', webpage, 'upload date',
            fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'upload_date': upload_date,
        }
