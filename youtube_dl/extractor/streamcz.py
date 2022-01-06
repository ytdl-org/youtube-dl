# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
)
from ..utils import (
    float_or_none,
    int_or_none,
    js_to_json,
    parse_codecs,
    str_or_none,
    try_get,
    urljoin,
)


class StreamCZBase(InfoExtractor):
    def _extract_sdn_formats(self, sdn_url, video_id):
        sdn_data = self._download_json(sdn_url, video_id)
        formats = []

        mp4_formats = try_get(sdn_data, lambda x: x['data']['mp4'], dict)
        for format_id, format_data in mp4_formats.items():
            format = {
                'url': urljoin(sdn_url, format_data.get('url')),
                'format_id': 'http-%s' % format_id,
                'container': 'mp4',
                'width': int_or_none(format_data.get('resolution')[0]),
                'height': int_or_none(format_data.get('resolution')[1]),
                'tbr': int_or_none(format_data.get('bandwidth'), scale=1000),
                'protocol': 'https',
            }
            format.update(parse_codecs(format_data.get('codec')))
            formats.append(format)

        def get_url(format_id):
            return try_get(pls, lambda x: x[format_id]['url'], compat_str)

        # PLS might contain further formats (DASH, HLS, HLS with fMP4)
        pls = sdn_data.get('pls')

        # DASH format
        dash_rel_url = get_url('dash')
        if dash_rel_url:
            formats.extend(self._extract_mpd_formats(
                urljoin(sdn_url, dash_rel_url), video_id, mpd_id='dash',
                fatal=False
            ))

        # HLS
        hls_rel_url = get_url('hls')
        if hls_rel_url:
            formats.extend(self._extract_m3u8_formats(
                urljoin(sdn_url, hls_rel_url), video_id, m3u8_id='hls',
                ext='ts', fatal=False
            ))

        self._sort_formats(formats)
        return formats


class StreamCZIE(StreamCZBase):
    _VALID_URL = r'https?://(?:www\.)?stream\.cz/(?:[^/]+)/.+-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.stream.cz/kdo-to-mluvi/kdo-to-mluvi-velke-odhaleni-prinasi-novy-porad-uz-od-25-srpna-64087937',
        'info_dict': {
            'id': '64087937',
            'title': 'Kdo to mluví? Velké odhalení přináší nový pořad už od 25. srpna',
            'description': 'K ikonickým tvářím obrazovek a filmových pláten neodmyslitelně patří i jejich hlasy. Kdo se ale za nimi skrývá? Sledujte nový seriál ze zákulisí dabingu už od příštího úterý.',
            'timestamp': 1597730400,
            'upload_date': '20200818',
            'duration': 51,
            'ext': 'mp4',
            'series': 'Kdo to mluví?'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        webpage_data = self._html_search_regex(r'(?s)window\s*\.\s*APP_SERVER_STATE\s*=\s*(\{.+?\})\s*;', webpage, 'webpage_data')
        webpage_json = self._parse_json(webpage_data, video_id, transform_source=js_to_json)

        video_detail = try_get(webpage_json, lambda x: x['data']['fetchable']['episode']['videoDetail']['data'], dict)

        # metadata
        title = video_detail['name']
        description = video_detail.get('perex')
        duration = video_detail.get('duration')
        published = try_get(video_detail, lambda x: x['publishTime']['timestamp'], int)
        thumbnails = video_detail.get('images')
        view_count = video_detail.get('views')
        is_live = video_detail.get('isLive')
        series = try_get(video_detail, lambda x: x['originTag']['name'], str)

        sdn_url = video_detail['spl'] + 'spl2,3,VOD'
        formats = self._extract_sdn_formats(sdn_url, video_id)

        return {
            'id': video_id,
            'title': title,
            'description': str_or_none(description),
            'thumbnails': thumbnails,
            'timestamp': published,
            'duration': float_or_none(duration),
            'view_count': int_or_none(view_count),
            'is_live': is_live,
            'series': str_or_none(series),
            'formats': formats,
        }
