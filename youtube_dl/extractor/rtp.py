# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RTPIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?rtp\.pt/play/p(?P<program_id>[0-9]+)/(?P<id>[^/?#]+)/?'
    _TESTS = [{
        'url': 'http://www.rtp.pt/play/p405/e174042/paixoes-cruzadas',
        'md5': 'e736ce0c665e459ddb818546220b4ef8',
        'info_dict': {
            'id': 'e174042',
            'ext': 'mp3',
            'title': 'Paixões Cruzadas',
            'description': 'As paixões musicais de António Cartaxo e António Macedo',
            'thumbnail': 're:^https?://.*\.jpg',
        },
        'params': {
            # rtmp download
            'skip_download': True,
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
        config = self._parse_json(player_config, video_id)

        path, ext = config.get('file').rsplit('.', 1)
        formats = [{
            'format_id': 'rtmp',
            'ext': ext,
            'vcodec': config.get('type') == 'audio' and 'none' or None,
            'preference': -2,
            'url': 'rtmp://{streamer:s}/{application:s}'.format(**config),
            'app': config.get('application'),
            'play_path': '{ext:s}:{path:s}'.format(ext=ext, path=path),
            'page_url': url,
            'rtmp_live': config.get('live', False),
            'player_url': 'http://programas.rtp.pt/play/player.swf?v3',
            'rtmp_real_time': True,
        }]

        # Construct regular HTTP download URLs
        replacements = {
            'audio': {
                'format_id': 'mp3',
                'pattern': r'^nas2\.share/wavrss/',
                'repl': 'http://rsspod.rtp.pt/podcasts/',
                'vcodec': 'none',
            },
            'video': {
                'format_id': 'mp4_h264',
                'pattern': r'^nas2\.share/h264/',
                'repl': 'http://rsspod.rtp.pt/videocasts/',
                'vcodec': 'h264',
            },
        }
        r = replacements[config['type']]
        if re.match(r['pattern'], config['file']) is not None:
            formats.append({
                'format_id': r['format_id'],
                'url': re.sub(r['pattern'], r['repl'], config['file']),
                'vcodec': r['vcodec'],
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
        }
