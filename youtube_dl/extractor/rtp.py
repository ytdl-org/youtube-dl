# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json


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
            'thumbnail': r're:^https?://.*\.jpg',
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
            r'(?s)RTPPlayer\(({.*?})', webpage, 'player config')
        player_config = js_to_json(player_config)
        config = self._parse_json(player_config, video_id)
        path, ext = config.get('file').rsplit('.', 1)
        formats = [{
            'format_id': 'rtmp',
            'ext': ext,
            'preference': -2,
            'url': '{file}'.format(**config),
            'app': config.get('application'),
            'play_path': '{ext:s}:{path:s}'.format(ext=ext, path=path),
            'page_url': url,
            'player_url': 'http://programas.rtp.pt/play/player.swf?v3',
            'rtmp_real_time': True,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': description,
            'thumbnail': thumbnail,
        }

class RTPPlaylistIE(RTPIE):
    #_VALID_URL = r'https?://(?:www\.)?rtp\.pt/play/p(?P<program_id>[0-9]+)/(?P<id>[^/?#]+)/?'
    _VALID_URL = r'1234'
    def _real_extract(self, url):

        return {
            '_type': 'playlist',
            'entries':[{'_type':'url', 'url':'https://www.rtp.pt/play/p510/e400299/aleixo-fm'}]
        }
