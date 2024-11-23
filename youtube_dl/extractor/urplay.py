# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    dict_get,
    ExtractorError,
    int_or_none,
    ISO639Utils,
    parse_age_limit,
    try_get,
    unified_timestamp,
)


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
            'timestamp': 1513292400,
            'upload_date': '20171214',
            'series': 'UR Samtiden - Livet, universum och rymdens märkliga musik',
            'duration': 2269,
            'categories': ['Vetenskap & teknik'],
            'tags': ['Kritiskt tänkande', 'Vetenskap', 'Vetenskaplig verksamhet'],
            'episode': 'Om vetenskap, kritiskt tänkande och motstånd',
            'age_limit': 15,
        },
    }, {
        'url': 'https://urskola.se/Produkter/190031-Tripp-Trapp-Trad-Sovkudde',
        'info_dict': {
            'id': '190031',
            'ext': 'mp4',
            'title': 'Tripp, Trapp, Träd : Sovkudde',
            'description': 'md5:b86bffdae04a7e9379d1d7e5947df1d1',
            'timestamp': 1440086400,
            'upload_date': '20150820',
            'series': 'Tripp, Trapp, Träd',
            'duration': 865,
            'tags': ['Sova'],
            'episode': 'Sovkudde',
        },
    }, {
        'url': 'http://urskola.se/Produkter/155794-Smasagor-meankieli-Grodan-i-vida-varlden',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace('skola.se/Produkter', 'play.se/program')
        webpage = self._download_webpage(url, video_id)
        urplayer_data = self._search_regex(
            r'(?s)\bid\s*=\s*"__NEXT_DATA__"[^>]*>\s*({.+?})\s*</script',
            webpage, 'urplayer next data', fatal=False) or {}
        if urplayer_data:
            urplayer_data = self._parse_json(urplayer_data, video_id, fatal=False)
            urplayer_data = try_get(urplayer_data, lambda x: x['props']['pageProps']['program'], dict)
            if not urplayer_data:
                raise ExtractorError('Unable to parse __NEXT_DATA__')
        else:
            accessible_episodes = self._parse_json(self._html_search_regex(
                r'data-react-class="routes/Product/components/ProgramContainer/ProgramContainer"[^>]+data-react-props="({.+?})"',
                webpage, 'urplayer data'), video_id)['accessibleEpisodes']
            urplayer_data = next(e for e in accessible_episodes if e.get('id') == int_or_none(video_id))
        episode = urplayer_data['title']
        raw_streaming_info = urplayer_data['streamingInfo']['raw']
        host = self._download_json(
            'http://streaming-loadbalancer.ur.se/loadbalancer.json',
            video_id)['redirect']

        formats = []
        for k, v in raw_streaming_info.items():
            if not (k in ('sd', 'hd') and isinstance(v, dict)):
                continue
            file_http = v.get('location')
            if file_http:
                formats.extend(self._extract_wowza_formats(
                    'http://%s/%splaylist.m3u8' % (host, file_http),
                    video_id, skip_protocols=['f4m', 'rtmp', 'rtsp']))
        self._sort_formats(formats)

        subtitles = {}

        def parse_lang_code(code):
            "3-character language code or None (utils candidate)"
            if code is None:
                return
            lang = code.lower()
            if not ISO639Utils.long2short(lang):
                lang = ISO639Utils.short2long(lang)
            return lang or None

        for k, v in (urplayer_data['streamingInfo'].get('sweComplete') or {}).items():
            if (k in ('sd', 'hd') or not isinstance(v, dict)):
                continue
            lang, sttl_url = (v.get(kk) for kk in ('language', 'location', ))
            if not sttl_url:
                continue
            lang = parse_lang_code(lang)
            if not lang:
                continue
            sttl = subtitles.get(lang) or []
            sttl.append({'ext': k, 'url': sttl_url, })
            subtitles[lang] = sttl

        image = urplayer_data.get('image') or {}
        thumbnails = []
        for k, v in image.items():
            t = {
                'id': k,
                'url': v,
            }
            wh = k.split('x')
            if len(wh) == 2:
                t.update({
                    'width': int_or_none(wh[0]),
                    'height': int_or_none(wh[1]),
                })
            thumbnails.append(t)

        series = urplayer_data.get('series') or {}
        series_title = dict_get(series, ('seriesTitle', 'title')) or dict_get(urplayer_data, ('seriesTitle', 'mainTitle'))

        return {
            'id': video_id,
            'title': '%s : %s' % (series_title, episode) if series_title else episode,
            'description': urplayer_data.get('description'),
            'thumbnails': thumbnails,
            'timestamp': unified_timestamp(urplayer_data.get('publishedAt')),
            'series': series_title,
            'formats': formats,
            'duration': int_or_none(urplayer_data.get('duration')),
            'categories': urplayer_data.get('categories'),
            'tags': urplayer_data.get('keywords'),
            'season': series.get('label'),
            'episode': episode,
            'episode_number': int_or_none(urplayer_data.get('episodeNumber')),
            'age_limit': parse_age_limit(min(try_get(a, lambda x: x['from'], int) or 0
                                             for a in urplayer_data.get('ageRanges', []))),
            'subtitles': subtitles,
        }
