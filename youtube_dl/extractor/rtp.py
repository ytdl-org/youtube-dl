# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import js_to_json


class RTPIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtp\.pt/play/p(?P<program_id>[0-9]+)/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'http://www.rtp.pt/play/p405/e174042/paixoes-cruzadas',
        'info_dict': {
            'id': 'e174042',
            'ext': 'mp3',
            'title': 'Paixões Cruzadas',
            'description': 'As paixões musicais de António Cartaxo e António Macedo',
            'thumbnail': 're:^https?://.*\.jpg',
        },
        'params': {
            'skip_download': True,  # RTMP download
        },
    }, {
        'url': 'http://www.rtp.pt/play/p831/a-quimica-das-coisas',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_meta(
            'twitter:title', webpage, display_name='title', fatal=True)
        description = self._html_search_meta('description', webpage)
        thumbnail = self._og_search_thumbnail(webpage)

        player_config = self._search_regex(
            r'(?s)RTPPLAY\.player\.newPlayer\(\s*(\{.*?\})\s*\)', webpage, 'player config')
        config = json.loads(js_to_json(player_config))

        path, ext = config.get('file').rsplit('.', 1)
        formats = [{
            'app': config.get('application'),
            'play_path': '{ext:s}:{path:s}'.format(ext=ext, path=path),
            'page_url': url,
            'url': 'rtmp://{streamer:s}/{application:s}'.format(**config),
            'rtmp_live': config.get('live', False),
            'ext': ext,
            'vcodec': config.get('type') == 'audio' and 'none' or None,
            'player_url': 'http://programas.rtp.pt/play/player.swf?v3',
            'rtmp_real_time': True,
        }]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
        }
