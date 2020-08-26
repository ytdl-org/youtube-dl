# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    int_or_none,
    parse_duration,
    update_url_query,
    str_or_none,
)


class UOLIE(InfoExtractor):
    IE_NAME = 'uol.com.br'
    _VALID_URL = r'https?://(?:.+?\.)?uol\.com\.br/.*?(?:(?:mediaId|v)=|view/(?:[a-z0-9]+/)?|video(?:=|/(?:\d{4}/\d{2}/\d{2}/)?))(?P<id>\d+|[\w-]+-[A-Z0-9]+)'
    _TESTS = [{
        'url': 'http://player.mais.uol.com.br/player_video_v3.swf?mediaId=15951931',
        'md5': '25291da27dc45e0afb5718a8603d3816',
        'info_dict': {
            'id': '15951931',
            'ext': 'mp4',
            'title': 'Miss simpatia é encontrada morta',
            'description': 'md5:3f8c11a0c0556d66daf7e5b45ef823b2',
        }
    }, {
        'url': 'http://tvuol.uol.com.br/video/incendio-destroi-uma-das-maiores-casas-noturnas-de-londres-04024E9A3268D4C95326',
        'md5': 'e41a2fb7b7398a3a46b6af37b15c00c9',
        'info_dict': {
            'id': '15954259',
            'ext': 'mp4',
            'title': 'Incêndio destrói uma das maiores casas noturnas de Londres',
            'description': 'Em Londres, um incêndio destruiu uma das maiores boates da cidade. Não há informações sobre vítimas.',
        }
    }, {
        'url': 'http://mais.uol.com.br/static/uolplayer/index.html?mediaId=15951931',
        'only_matching': True,
    }, {
        'url': 'http://mais.uol.com.br/view/15954259',
        'only_matching': True,
    }, {
        'url': 'http://noticias.band.uol.com.br/brasilurgente/video/2016/08/05/15951931/miss-simpatia-e-encontrada-morta.html',
        'only_matching': True,
    }, {
        'url': 'http://videos.band.uol.com.br/programa.asp?e=noticias&pr=brasil-urgente&v=15951931&t=Policia-desmonte-base-do-PCC-na-Cracolandia',
        'only_matching': True,
    }, {
        'url': 'http://mais.uol.com.br/view/cphaa0gl2x8r/incendio-destroi-uma-das-maiores-casas-noturnas-de-londres-04024E9A3268D4C95326',
        'only_matching': True,
    }, {
        'url': 'http://noticias.uol.com.br//videos/assistir.htm?video=rafaela-silva-inspira-criancas-no-judo-04024D983968D4C95326',
        'only_matching': True,
    }, {
        'url': 'http://mais.uol.com.br/view/e0qbgxid79uv/15275470',
        'only_matching': True,
    }]

    _FORMATS = {
        '2': {
            'width': 640,
            'height': 360,
        },
        '5': {
            'width': 1280,
            'height': 720,
        },
        '6': {
            'width': 426,
            'height': 240,
        },
        '7': {
            'width': 1920,
            'height': 1080,
        },
        '8': {
            'width': 192,
            'height': 144,
        },
        '9': {
            'width': 568,
            'height': 320,
        },
        '11': {
            'width': 640,
            'height': 360,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        media_id = None

        if video_id.isdigit():
            media_id = video_id

        if not media_id:
            embed_page = self._download_webpage(
                'https://jsuol.com.br/c/tv/uol/embed/?params=[embed,%s]' % video_id,
                video_id, 'Downloading embed page', fatal=False)
            if embed_page:
                media_id = self._search_regex(
                    (r'uol\.com\.br/(\d+)', r'mediaId=(\d+)'),
                    embed_page, 'media id', default=None)

        if not media_id:
            webpage = self._download_webpage(url, video_id)
            media_id = self._search_regex(r'mediaId=(\d+)', webpage, 'media id')

        video_data = self._download_json(
            'http://mais.uol.com.br/apiuol/v3/player/getMedia/%s.json' % media_id,
            media_id)['item']
        title = video_data['title']

        query = {
            'ver': video_data.get('numRevision', 2),
            'r': 'http://mais.uol.com.br',
        }
        for k in ('token', 'sign'):
            v = video_data.get(k)
            if v:
                query[k] = v

        formats = []
        for f in video_data.get('formats', []):
            f_url = f.get('url') or f.get('secureUrl')
            if not f_url:
                continue
            f_url = update_url_query(f_url, query)
            format_id = str_or_none(f.get('id'))
            if format_id == '10':
                formats.extend(self._extract_m3u8_formats(
                    f_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
                continue
            fmt = {
                'format_id': format_id,
                'url': f_url,
                'source_preference': 1,
            }
            fmt.update(self._FORMATS.get(format_id, {}))
            formats.append(fmt)
        self._sort_formats(formats, ('height', 'width', 'source_preference', 'tbr', 'ext'))

        tags = []
        for tag in video_data.get('tags', []):
            tag_description = tag.get('description')
            if not tag_description:
                continue
            tags.append(tag_description)

        return {
            'id': media_id,
            'title': title,
            'description': clean_html(video_data.get('desMedia')),
            'thumbnail': video_data.get('thumbnail'),
            'duration': int_or_none(video_data.get('durationSeconds')) or parse_duration(video_data.get('duration')),
            'tags': tags,
            'formats': formats,
        }
