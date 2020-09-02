# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unified_timestamp


class URPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ur(?:play|skola)\.se/(?:program|Produkter)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://urplay.se/program/203704-ur-samtiden-livet-universum-och-rymdens-markliga-musik-om-vetenskap-kritiskt-tankande-och-motstand',
        'md5': 'ff5b0c89928f8083c74bbd5099c9292d',
        'info_dict': {
            'id': '203704',
            'ext': 'mp4',
            'title': 'UR Samtiden - Livet, universum och rymdens märkliga musik : Om vetenskap, kritiskt tänkande och motstånd',
            'description': 'md5:5344508a52aa78c1ced6c1b8b9e44e9a',
            'timestamp': 1513512768,
            'upload_date': '20171217',
        },
    }, {
        'url': 'https://urskola.se/Produkter/190031-Tripp-Trapp-Trad-Sovkudde',
        'info_dict': {
            'id': '190031',
            'ext': 'mp4',
            'title': 'Tripp, Trapp, Träd : Sovkudde',
            'description': 'md5:b86bffdae04a7e9379d1d7e5947df1d1',
            'timestamp': 1440093600,
            'upload_date': '20150820',
        },
    }, {
        'url': 'http://urskola.se/Produkter/155794-Smasagor-meankieli-Grodan-i-vida-varlden',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        urplayer_data = self._parse_json(self._search_regex(
            r'urPlayer\.init\(({.+?})\);', webpage, 'urplayer data'), video_id)
        host = self._download_json('http://streaming-loadbalancer.ur.se/loadbalancer.json', video_id)['redirect']

        formats = []
        for quality_attr, quality, preference in (('', 'sd', 0), ('_hd', 'hd', 1)):
            file_http = urplayer_data.get('file_http' + quality_attr) or urplayer_data.get('file_http_sub' + quality_attr)
            if file_http:
                formats.extend(self._extract_wowza_formats(
                    'http://%s/%splaylist.m3u8' % (host, file_http), video_id, skip_protocols=['rtmp', 'rtsp']))
        self._sort_formats(formats)

        subtitles = {}
        for subtitle in urplayer_data.get('subtitles', []):
            subtitle_url = subtitle.get('file')
            kind = subtitle.get('kind')
            if not subtitle_url or (kind and kind != 'captions'):
                continue
            subtitles.setdefault(subtitle.get('label', 'Svenska'), []).append({
                'url': subtitle_url,
            })

        return {
            'id': video_id,
            'title': urplayer_data['title'],
            'description': self._og_search_description(webpage),
            'thumbnail': urplayer_data.get('image'),
            'timestamp': unified_timestamp(self._html_search_meta(('uploadDate', 'schema:uploadDate'), webpage, 'timestamp')),
            'series': urplayer_data.get('series_title'),
            'subtitles': subtitles,
            'formats': formats,
        }
