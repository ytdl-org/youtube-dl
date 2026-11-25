# coding: utf-8
from __future__ import unicode_literals

import json
import re
import time

from .common import InfoExtractor

from ..compat import (
    compat_urlparse,
)
from ..utils import (
    determine_ext,
    dict_get,
    merge_dicts,
    parse_iso8601,
    strip_or_none,
    try_get,
    url_or_none,
    urljoin,
)


class TRTIE(InfoExtractor):
    IE_DESC = 'TRT (Turkish State TV) programs and series'
    _VALID_URL = r'''(?x)
                     (?P<list>https?://(?:www\.)trtizle\.com/
                         (?:diziler|programlar|belgesel|filmler|cocuk|trtarsiv|engelsiz)/
                             (?P<show>[\w-]+))(?:/(?P<id>[\w-]+))?'''
    _TESTS = [{
        'url': 'https://www.trtizle.com/belgesel/dunya-tarihinin-donum-noktalari/dunya-tarihinin-donum-noktalari-1-bolum-125583',
        'md5': 'c46dc0b9b53ad372c4ac6b3982805f05',
        'info_dict': {
            'id': 'dunya-tarihinin-donum-noktalari-1-bolum-125583',
            'ext': 'mp4',
            'title': 'Dünya Tarihinin Dönüm Noktaları 1.Bölüm',
            'description': 'Bedelini insanların ödeyeceği bir imparatorluk çekişmesinde Persler, Yunanlara karşı...',
            'timestamp': 1617148800,
            'upload_date': '20210331',
            'thumbnail': r're:https?://.+\.jpe?g',
            'duration': float,
            'series': 'Dünya Tarihinin Dönüm Noktaları',
        },
        'params': {
            # adaptive download
            'skip_download': True,
        }
    }, {
        'url': 'https://www.trtizle.com/belgesel/dunya-tarihinin-donum-noktalari',
        'info_dict': {
            'id': 'dunya-tarihinin-donum-noktalari',
            'title': 'Dünya Tarihinin Dönüm Noktaları',
        },
        'playlist_mincount': 22,
    }, {
        'url': 'https://www.trtizle.com/diziler/yol-ayrimi/yol-ayrimi-1-bolum-5774583',
        'md5': '67ada6b2020b5dd0d3e24646b2725676',
        'info_dict': {
            'id': 'yol-ayrimi-1-bolum-5774583',
            'ext': 'mp4',
            'title': 'Yol Ayrımı 1.Bölüm',
            'description': 'Seyrisefain balosunda, herkes bir haberin akıbetini beklemektedir…',
            'timestamp': 1623888000,
            'upload_date': '20210617',
            'thumbnail': r're:https?://.+\.jpe?g',
            'duration': float,
            'series': 'Yol Ayrımı',
        },
        'params': {
            # adaptive download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.trtizle.com/diziler/yol-ayrimi/',
        'info_dict': {
            'id': 'yol-ayrimi',
            'title': 'Yol Ayrımı',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://www.trtizle.com/programlar/sade-saz/sade-saz-1-bolum-7646201',
        'md5': '8f416e64379ea4d1d3ea0a65dc922f5c',
        'info_dict': {
            'id': 'sade-saz-1-bolum-7646201',
            'ext': 'mp4',
            'title': 'Sade Saz 1.Bölüm',
            'description': 'Sade Saz’ın ilk bölümünün konuğu, tanbur icracısı K. Alper Uzkur.',
            'timestamp': 1641772800,
            'upload_date': '20220110',
            'thumbnail': r're:https?://.+\.jpe?g',
            'duration': float,
            'series': 'Sade Saz',
        },
        'params': {
            # adaptive download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.trtizle.com/programlar/sade-saz',
        'info_dict': {
            'id': 'sade-saz',
            'title': 'Sade Saz',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://www.trtizle.com/filmler/looking-for-eric/looking-for-eric-8414201',
        'md5': '833d61e4a10606d71b3903295cfa3c63',
        'info_dict': {
            'id': 'looking-for-eric-8414201',
            'ext': 'mp4',
            'title': 'Looking for Eric',
            'description': 'Postacı Eric\'in hayatı krize sürüklenirken gerçek ve hayal birbirine karışır...',
            'upload_date': '20220401',
            'timestamp': 1648771200,
            'thumbnail': r're:https?://.+\.jpe?g',
            'duration': float,
        },
        'params': {
            # adaptive download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.trtizle.com/cocuk/kaptan-pengu-ve-arkadaslari/kaptan-pengu-ve-arkadaslari-okul-aciliyor-6034815',
        'md5': '551c479d1a6bc7c538356907d4ea5d19',
        'info_dict': {
            'id': 'kaptan-pengu-ve-arkadaslari-okul-aciliyor-6034815',
            'ext': 'mp4',
            'title': 'Kaptan Pengu ve Arkadaşları 1.Bölüm',
            'description': 'Hayvanlar Konseyi\'nden Kaptan Pengu\'ya bir mektup vardır...',
            'timestamp': 1626134400,
            'upload_date': '20210713',
            'thumbnail': r're:https?://.+\.jpe?g',
            'duration': float,
            'series': 'Kaptan Pengu ve Arkadaşları',
        },
        'params': {
            # adaptive download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.trtizle.com/cocuk/kaptan-pengu-ve-arkadaslari',
        'info_dict': {
            'id': 'kaptan-pengu-ve-arkadaslari',
            'title': 'Kaptan Pengu ve Arkadaşları',
        },
        'playlist_mincount': 41,
    },
    ]

    def _extract_formats(self, fmt_url, video_id):
        formats = []
        ext = determine_ext(fmt_url)
        if ext == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                fmt_url, video_id, 'mp4', entry_protocol='m3u8_native',
                m3u8_id='hls', fatal=False))
        elif ext == 'mpd':
            formats.extend(self._extract_mpd_formats(
                fmt_url, video_id, mpd_id='dash', fatal=False))
        else:
            formats.append({
                'url': fmt_url,
            })
        return formats

    def _extract_list(self, playlist_id, url):
        webpage = self._download_webpage(url, playlist_id)
        LIST_RE = (
            r'''<a\s[^>]*?\b%s\s*=\s*['"](%s(?:(?<=/)|/)[\w-]+)'''
            % ('data-path' if 'data-path' in webpage else 'href',
               re.escape(compat_urlparse.urlparse(url).path), ))

        def entries():
            for item_url in re.finditer(LIST_RE, webpage):
                item_url = urljoin(url, item_url.group(1))
                yield self._extract_video(self._match_id(item_url), item_url)

        series = self._search_json_ld(webpage, playlist_id, default={}, expected_type='TVSeries')
        return self.playlist_result(entries(), playlist_id, series.get('series'))

    def _extract_video(self, video_id, url):
        webpage = self._download_webpage(url, video_id)
        result = self._search_json_ld(webpage, video_id, default={})
        result['id'] = video_id
        if 'title' not in result:
            result['title'] = (
                self._html_search_meta(('title', 'og:title', 'twitter:title'), webpage)
                or self._html_search_regex(r'<title\b[^>]*>([^<]+)</title\b', webpage, 'title'))
        fmt_url = result.get('url')
        formats = []
        if fmt_url:
            del result['url']
            formats = self._extract_formats(fmt_url, video_id)
        self._sort_formats(formats)
        result['formats'] = formats

        return merge_dicts(
            result, {
                'description': self._html_search_meta(('description', 'og:description'), webpage, 'description'),
                'thumbnail': url_or_none(self._og_search_thumbnail(webpage)),
            })

    def _real_extract(self, url):
        show_id, video_id, playlist_url = re.match(self._VALID_URL, url).group('show', 'id', 'list')
        # TODO: adapt --yes/no-playlist to make this work properly
        # if not video_id or self._downloader.params.get('noplaylist') is False:
        if not video_id:
            return self._extract_list(show_id, playlist_url)

        return self._extract_video(video_id, url)


class TRTLiveIE(TRTIE):
    IE_DESC = 'TRT (Turkish State TV and radio) live channels'
    _VALID_URL = r'https?://(?:www\.)?trtizle\.com/canli/(?:tv/trt-|radyo/(?:radyo-)?)(?P<id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.trtizle.com/canli/tv/trt-world',
        'info_dict': {
            'id': 'trtworld',
            'ext': 'mp4',
            'title': r're:TRT WORLD .+',
            'description': 'TRT World',
            'is_live': True,
        },
        'params': {
            # adaptive download
            'skip_download': True,
        }
    },
    ]

    def _real_extract(self, url):
        chan_id = self._match_id(url)
        webpage = self._download_webpage(url, chan_id)
        chan_id = self._search_regex(
            r'\blivePlayer\s*\.\s*openPlayer\s*\([^)]*?\btrt\.com\.tr/trtportal/(?:[^/]+/)+thumbnails/([\w-]+)\.(?:jp|png)',
            webpage, 'slug', fatal=False) or chan_id
        chan_url = self._search_regex(
            r'''\blivePlayerConfig\s*\.\s*baseEpgUrl\s*=\s*(?P<q>'|")(?P<url>https?://(?:(?!(?P=q)).)+)(?P=q)''',
            webpage, 'player config', group='url')
        chan_url = '%s%s.json' % (chan_url, chan_id)

        def maybe_xml2json(src):
            """Turn unexpected XML returned from an API URL into JSON"""
            m = re.match(r'''^\s*<\?xml\b(?:[^/>]*?\bencoding\s*=\s*['"](?P<enc>[\w-]+))?[^/>]*\?>\s*(?P<xml><.+>)$''', src)
            if m:

                # Thanks https://stackoverflow.com/a/63556250 for inspiration
                ATTR_RE = (
                    r"""(?s)(?P<avr>\S ?)(?:\s*=\s*(?P<q>['"])(?P<avl>.*?)(?<!\\)(?P=q))?"""
                )

                def elt_value(attr_str, val_dict):
                    v = {}
                    attrs = dict((j.group("avr"), j.groupdict(True).get("avl"))
                                 for j in re.finditer(ATTR_RE, attr_str.strip()))
                    if attrs:
                        v['@attributes'] = attrs
                    v['@values'] = val_dict
                    return v

                def xml2dict(xml_str):
                    elts = re.findall(
                        r"(?s)<(?P<var>\S )(?P<attr>[^/>]*)(?:(?:>(?P<val>.*?)</(?P=var)>)|(?:/>))",
                        xml_str,
                    )

                    if elts:
                        elts = [{i[0]: elt_value(i[1], xml2dict(i[2]))} for i in elts]
                        if len(elts) == 1:
                            return elts[0]
                        return elts
                    return xml_str

                try:
                    return json.dumps(xml2dict(m.group('xml').encode(m.group('enc') or 'utf-8')))
                except Exception:
                    pass
            return src

        chan_info = self._download_json(
            chan_url, chan_id, fatal=False,
            note='Downloading player EPG JSON',
            query={'_': int(time.time() * 1000)},
            expected_status=403,
            # errors are returned as XML
            transform_source=maybe_xml2json)
        if not isinstance(chan_info, dict) or 'Error' in chan_info:
            chan_info = self._download_json(
                'https://trtizle-api.cdn.wp.trt.com.tr/trttv/v3/livestream',
                chan_id, fatal=False,
                note='Downloading livestream API JSON',
                query={'path': compat_urlparse.urlparse(url).path}) or {}

        title = chan_info['channel']['title']

        current = try_get(chan_info, lambda x: x['current'], dict) or {}
        if current.get('geo_block'):
            self._downloader.report_warning(
                '[%s] %s' % (self.IE_NAME, 'Stream is geo-blocked'))

        chan_info = chan_info['channel']
        fmt_url = dict_get(chan_info, ('url', 'noneDvrUrl'))
        formats = []
        if fmt_url:
            formats = self._extract_formats(fmt_url, chan_id)
        self._sort_formats(formats)

        start_end = [parse_iso8601(current.get(x)) for x in ('starttime', 'endtime')]
        if None in start_end:
            start_end = None

        return {
            'id': chan_id,
            'title': self._live_title(current.get('title') or title),
            'is_live': True,
            'formats': formats,
            'description': strip_or_none(chan_info.get('description')),
            'thumbnail': next((url_or_none(chan_info.get(x))
                              for x in ('thumbnail', 'thumbnailYoutubeUrl', 'square_logo', 'livestreamLogoUrl')),
                              None),
            'timestamp': start_end and start_end[0],
            'duration': start_end and (start_end[1] - time.time()),
        }
