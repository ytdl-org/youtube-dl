from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    parse_duration,
    try_get,
    url_or_none,
)


class NuvidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|m)\.nuvid\.com/video/(?P<id>[0-9]+)'
    _PLAYER_CONFIG_URL_TEMPLATE = (
        'https://www.nuvid.com/player_config_json/?vid=%s'
        '&aid=0&domain_id=0&embed=0&ref=null&check_speed=0')
    _TEST = {
        'url': 'http://m.nuvid.com/video/6415801/',
        'info_dict': {
            'id': '6415801',
            'format_id': 'hq',
            'ext': 'mp4',
            'title': 'My best friend wanted to fuck my wife for a long time',
            'duration': 1882,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # nice to have, not required
        page_url = 'http://m.nuvid.com/video/%s' % video_id
        webpage = self._download_webpage(
            page_url, video_id, 'Downloading video page', fatal=False)
        json_url = self._PLAYER_CONFIG_URL_TEMPLATE % video_id
        # necessary
        player_json = self._download_json(
            json_url, video_id, 'Downloading player JSON')
        title = (try_get(player_json, lambda x: x['title'], compat_str)
                 or self._html_search_regex(
            [r'<span title="([^"]+)">',
             r'<div class="thumb-holder video">\s*<h5[^>]*>([^<]+)</h5>',
             r'<span[^>]+class="title_thumb">([^<]+)</span>'],
            webpage, 'title'))
        if not title:
            return
        formats = []
        for (k, v) in (try_get(
                player_json, lambda x: x['files'], dict) or {}).items():
            v = url_or_none(v)
            if v:
                formats.append({
                    'format_id': k,
                    'resolution': k,
                    'quality': -2 if k == 'lq' else -1,
                    'url': v,
                })
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title.strip(),
            'thumbnail': player_json.get('poster'),
            'duration': parse_duration(player_json.get('duration')),
            'age_limit': 18,
            'formats': formats,
        }
