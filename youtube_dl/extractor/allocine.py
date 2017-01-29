# coding: utf-8
from __future__ import unicode_literals

from ..utils import qualities, remove_end, url_basename
from .common import InfoExtractor


class AllocineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?allocine\.fr/(?:article|video|film)/(?:fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\.html)?'

    _TESTS = [{
        'url': 'http://www.allocine.fr/article/fichearticle_gen_carticle=18635087.html',
        'md5': '0c9fcf59a841f65635fa300ac43d8269',
        'info_dict': {
            'id': '19546517',
            'display_id': '18635087',
            'ext': 'mp4',
            'title': 'Astérix - Le Domaine des Dieux Teaser VF',
            'description': 'md5:4a754271d9c6f16c72629a8a993ee884',
            'thumbnail': r're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/video/player_gen_cmedia=19540403&cfilm=222257.html',
        'md5': 'd0cdce5d2b9522ce279fdfec07ff16e0',
        'info_dict': {
            'id': '19540403',
            'display_id': '19540403',
            'ext': 'mp4',
            'title': 'Planes 2 Bande-annonce VF',
            'description': 'Regardez la bande annonce du film Planes 2 (Planes 2 Bande-annonce VF). Planes 2, un film de Roberts Gannaway',
            'thumbnail': r're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/video/player_gen_cmedia=19544709&cfilm=181290.html',
        'md5': '101250fb127ef9ca3d73186ff22a47ce',
        'info_dict': {
            'id': '19544709',
            'display_id': '19544709',
            'ext': 'mp4',
            'title': 'Dragons 2 - Bande annonce finale VF',
            'description': 'md5:6cdd2d7c2687d4c6aafe80a35e17267a',
            'thumbnail': r're:http://.*\.jpg',
        },
    }, {
        'url': 'http://www.allocine.fr/video/video-19550147/',
        'md5': '3566c0668c0235e2d224fd8edb389f67',
        'info_dict': {
            'id': '19550147',
            'ext': 'mp4',
            'title': 'Faux Raccord N°123 - Les gaffes de Cliffhanger',
            'description': 'md5:bc734b83ffa2d8a12188d9eb48bb6354',
            'thumbnail': r're:http://.*\.jpg',
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        formats = []
        quality = qualities(['ld', 'md', 'hd'])

        model = self._html_search_regex(
            r'data-model="([^"]+)"', webpage, 'data model', default=None)
        if model:
            model_data = self._parse_json(model, display_id)

            for video_url in model_data['sources'].values():
                video_id, format_id = url_basename(video_url).split('_')[:2]
                formats.append({
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'url': video_url,
                })

            title = model_data['title']
        else:
            video_id = display_id
            media_data = self._download_json(
                'http://www.allocine.fr/ws/AcVisiondataV5.ashx?media=%s' % video_id, display_id)
            for key, value in media_data['video'].items():
                if not key.endswith('Path'):
                    continue

                format_id = key[:-len('Path')]
                formats.append({
                    'format_id': format_id,
                    'quality': quality(format_id),
                    'url': value,
                })

            title = remove_end(self._html_search_regex(
                r'(?s)<title>(.+?)</title>', webpage, 'title'
            ).strip(), ' - AlloCiné')

        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }
