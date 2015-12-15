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
        config = self._download_json(
            'http://client.expotv.com/video/config/%s/%s' % (video_id, player_key),
            video_id, 'Downloading video configuration')

        formats = []
        for fcfg in config['sources']:
            media_url = fcfg.get('file')
            if not media_url:
                continue
            if fcfg.get('type') == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls'))
            else:
                formats.append({
                    'url': media_url,
                    'height': int_or_none(fcfg.get('height')),
                    'format_id': fcfg.get('label'),
                    'ext': self._search_regex(
                        r'filename=.*\.([a-z0-9_A-Z]+)&', media_url,
                        'file extension', default=None) or fcfg.get('type'),
                })
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
