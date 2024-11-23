# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    ExtractorError,
    extract_attributes,
    float_or_none,
    int_or_none,
    merge_dicts,
    NO_DEFAULT,
    parse_codecs,
    qualities,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
    urljoin,
)


class ZDFBaseIE(InfoExtractor):
    _GEO_COUNTRIES = ['DE']
    _QUALITIES = ('auto', 'low', 'med', 'high', 'veryhigh', 'hd')

    def _call_api(self, url, video_id, item, api_token=None, referrer=None):
        headers = {}
        if api_token:
            headers['Api-Auth'] = 'Bearer %s' % api_token
        if referrer:
            headers['Referer'] = referrer
        return self._download_json(
            url, video_id, 'Downloading JSON %s' % item, headers=headers)

    @staticmethod
    def _extract_subtitles(src):
        subtitles = {}
        for caption in try_get(src, lambda x: x['captions'], list) or []:
            subtitle_url = url_or_none(caption.get('uri'))
            if subtitle_url:
                lang = caption.get('language', 'deu')
                subtitles.setdefault(lang, []).append({
                    'url': subtitle_url,
                })
        return subtitles

    def _extract_format(self, video_id, formats, format_urls, meta):
        format_url = url_or_none(meta.get('url'))
        if not format_url:
            return
        if format_url in format_urls:
            return
        format_urls.add(format_url)
        mime_type = meta.get('mimeType')
        ext = determine_ext(format_url)

        join_nonempty = lambda s, l: s.join(filter(None, l))
        meta_map = lambda t: map(lambda x: str_or_none(meta.get(x)), t)

        if mime_type == 'application/x-mpegURL' or ext == 'm3u8':
            new_formats = self._extract_m3u8_formats(
                format_url, video_id, 'mp4', m3u8_id='hls',
                entry_protocol='m3u8_native', fatal=False)
        elif mime_type == 'application/f4m+xml' or ext == 'f4m':
            new_formats = self._extract_f4m_formats(
                update_url_query(format_url, {'hdcore': '3.7.0'}), video_id, f4m_id='hds', fatal=False)
        else:
            f = parse_codecs(meta.get('mimeCodec'))
            if not f:
                data = meta.get('type', '').split('_')
                if try_get(data, lambda x: x[2]) == ext:
                    f = dict(zip(('vcodec', 'acodec'), data[1]))

            format_id = ['http']
            format_id.extend(join_nonempty('-', meta_map(('type', 'quality'))))
            f.update({
                'url': format_url,
                'format_id': '-'.join(format_id),
                'tbr': int_or_none(self._search_regex(r'_(\d+)k_', format_url, 'tbr', default=None))
            })
            new_formats = [f]

        formats.extend(merge_dicts(f, {
            'format_note': join_nonempty(',', meta_map(('quality', 'class'))),
            'language': meta.get('language'),
            'language_preference': 10 if meta.get('class') == 'main' else -10 if meta.get('class') == 'ad' else -1,
            'quality': qualities(self._QUALITIES)(meta.get('quality')),
        }) for f in new_formats)

    def _extract_ptmd(self, ptmd_url, video_id, api_token, referrer):
        ptmd = self._call_api(
            ptmd_url, video_id, 'metadata', api_token, referrer)

        content_id = ptmd.get('basename') or ptmd_url.split('/')[-1]

        formats = []
        track_uris = set()
        for p in ptmd['priorityList']:
            formitaeten = p.get('formitaeten')
            if not isinstance(formitaeten, list):
                continue
            for f in formitaeten:
                f_qualities = f.get('qualities')
                if not isinstance(f_qualities, list):
                    continue
                for quality in f_qualities:
                    tracks = try_get(quality, lambda x: x['audio']['tracks'], list)
                    if not tracks:
                        continue
                    for track in tracks:
                        self._extract_format(
                            content_id, formats, track_uris, {
                                'url': track.get('uri'),
                                'type': f.get('type'),
                                'mimeType': f.get('mimeType'),
                                'quality': quality.get('quality'),
                                'class': track.get('class'),
                                'language': track.get('language'),
                            })
        self._sort_formats(formats)

        duration = float_or_none(try_get(
            ptmd, lambda x: x['attributes']['duration']['value']), scale=1000)

        return {
            'extractor_key': ZDFIE.ie_key(),
            'id': content_id,
            'duration': duration,
            'formats': formats,
            'subtitles': self._extract_subtitles(ptmd),
        }

    def _extract_player(self, webpage, video_id, fatal=True):
        return self._parse_json(
            self._search_regex(
                r'(?s)data-zdfplayer-jsb=(["\'])(?P<json>{.+?})\1', webpage,
                'player JSON', default='{}' if not fatal else NO_DEFAULT,
                group='json'),
            video_id)


class ZDFIE(ZDFBaseIE):
    _VALID_URL = r'https?://www\.zdf\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)\.html'
    _TESTS = [{
        # Same as https://www.phoenix.de/sendungen/ereignisse/corona-nachgehakt/wohin-fuehrt-der-protest-in-der-pandemie-a-2050630.html
        'url': 'https://www.zdf.de/politik/phoenix-sendungen/wohin-fuehrt-der-protest-in-der-pandemie-100.html',
        'md5': '34ec321e7eb34231fd88616c65c92db0',
        'info_dict': {
            'id': '210222_phx_nachgehakt_corona_protest',
            'ext': 'mp4',
            'title': 'Wohin führt der Protest in der Pandemie?',
            'description': 'md5:7d643fe7f565e53a24aac036b2122fbd',
            'duration': 1691,
            'timestamp': 1613948400,
            'upload_date': '20210221',
        },
        'skip': 'No longer available: "Diese Seite wurde leider nicht gefunden"',
    }, {
        # Same as https://www.3sat.de/film/ab-18/10-wochen-sommer-108.html
        'url': 'https://www.zdf.de/dokumentation/ab-18/10-wochen-sommer-102.html',
        'md5': '0aff3e7bc72c8813f5e0fae333316a1d',
        'info_dict': {
            'id': '141007_ab18_10wochensommer_film',
            'ext': 'mp4',
            'title': 'Ab 18! - 10 Wochen Sommer',
            'description': 'md5:8253f41dc99ce2c3ff892dac2d65fe26',
            'duration': 2660,
            'timestamp': 1608604200,
            'upload_date': '20201222',
        },
        'skip': 'No longer available: "Diese Seite wurde leider nicht gefunden"',
    }, {
        'url': 'https://www.zdf.de/dokumentation/terra-x/die-magie-der-farben-von-koenigspurpur-und-jeansblau-100.html',
        'info_dict': {
            'id': '151025_magie_farben2_tex',
            'ext': 'mp4',
            'title': 'Die Magie der Farben (2/2)',
            'description': 'md5:a89da10c928c6235401066b60a6d5c1a',
            'duration': 2615,
            'timestamp': 1465021200,
            'upload_date': '20160604',
            'thumbnail': 'https://www.zdf.de/assets/mauve-im-labor-100~768x432?cb=1464909117806',
        },
    }, {
        'url': 'https://www.zdf.de/funk/druck-11790/funk-alles-ist-verzaubert-102.html',
        'md5': '1b93bdec7d02fc0b703c5e7687461628',
        'info_dict': {
            'ext': 'mp4',
            'id': 'video_funk_1770473',
            'duration': 1278,
            'description': 'Die Neue an der Schule verdreht Ismail den Kopf.',
            'title': 'Alles ist verzaubert',
            'timestamp': 1635520560,
            'upload_date': '20211029',
            'thumbnail': 'https://www.zdf.de/assets/teaser-funk-alles-ist-verzaubert-100~1920x1080?cb=1636466431799',
        },
    }, {
        # Same as https://www.phoenix.de/sendungen/dokumentationen/gesten-der-maechtigen-i-a-89468.html?ref=suche
        'url': 'https://www.zdf.de/politik/phoenix-sendungen/die-gesten-der-maechtigen-100.html',
        'only_matching': True,
    }, {
        # Same as https://www.3sat.de/film/spielfilm/der-hauptmann-100.html
        'url': 'https://www.zdf.de/filme/filme-sonstige/der-hauptmann-112.html',
        'only_matching': True,
    }, {
        # Same as https://www.3sat.de/wissen/nano/nano-21-mai-2019-102.html, equal media ids
        'url': 'https://www.zdf.de/wissen/nano/nano-21-mai-2019-102.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/service-und-hilfe/die-neue-zdf-mediathek/zdfmediathek-trailer-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/filme/taunuskrimi/die-lebenden-und-die-toten-1---ein-taunuskrimi-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/dokumentation/planet-e/planet-e-uebersichtsseite-weitere-dokumentationen-von-planet-e-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/arte/todliche-flucht/page-video-artede-toedliche-flucht-16-100.html',
        'info_dict': {
            'id': 'video_artede_083871-001-A',
            'ext': 'mp4',
            'title': 'Tödliche Flucht (1/6)',
            'description': 'md5:e34f96a9a5f8abd839ccfcebad3d5315',
            'duration': 3193.0,
            'timestamp': 1641355200,
            'upload_date': '20220105',
        },
        'skip': 'No longer available "Diese Seite wurde leider nicht gefunden"'
    }, {
        'url': 'https://www.zdf.de/serien/soko-stuttgart/das-geld-anderer-leute-100.html',
        'info_dict': {
            'id': '191205_1800_sendung_sok8',
            'ext': 'mp4',
            'title': 'Das Geld anderer Leute',
            'description': 'md5:cb6f660850dc5eb7d1ab776ea094959d',
            'duration': 2581.0,
            'timestamp': 1654790700,
            'upload_date': '20220609',
            'thumbnail': 'https://epg-image.zdf.de/fotobase-webdelivery/images/e2d7e55a-09f0-424e-ac73-6cac4dd65f35?layout=2400x1350',
        },
    }]

    def _extract_entry(self, url, player, content, video_id):
        title = content.get('title') or content['teaserHeadline']

        t = content['mainVideoContent']['http://zdf.de/rels/target']

        def get_ptmd_path(d):
            return (
                d.get('http://zdf.de/rels/streams/ptmd')
                or d.get('http://zdf.de/rels/streams/ptmd-template',
                         '').replace('{playerId}', 'ngplayer_2_4'))

        ptmd_path = get_ptmd_path(try_get(t, lambda x: x['streams']['default'], dict) or {})
        if not ptmd_path:
            ptmd_path = get_ptmd_path(t)

        if not ptmd_path:
            raise ExtractorError('Could not extract ptmd_path')

        info = self._extract_ptmd(
            urljoin(url, ptmd_path), video_id, player['apiToken'], url)

        thumbnails = []
        layouts = try_get(
            content, lambda x: x['teaserImageRef']['layouts'], dict)
        if layouts:
            for layout_key, layout_url in layouts.items():
                layout_url = url_or_none(layout_url)
                if not layout_url:
                    continue
                thumbnail = {
                    'url': layout_url,
                    'format_id': layout_key,
                }
                mobj = re.search(r'(?P<width>\d+)x(?P<height>\d+)', layout_key)
                if mobj:
                    thumbnail.update({
                        'width': int(mobj.group('width')),
                        'height': int(mobj.group('height')),
                    })
                thumbnails.append(thumbnail)

        return merge_dicts(info, {
            'title': title,
            'description': content.get('leadParagraph') or content.get('teasertext'),
            'duration': int_or_none(t.get('duration')),
            'timestamp': unified_timestamp(content.get('editorialDate')),
            'thumbnails': thumbnails,
        })

    def _extract_regular(self, url, player, video_id):
        content = self._call_api(
            player['content'], video_id, 'content', player['apiToken'], url)
        return self._extract_entry(player['content'], player, content, video_id)

    def _extract_mobile(self, video_id):
        video = self._download_json(
            'https://zdf-cdn.live.cellular.de/mediathekV2/document/%s' % video_id,
            video_id)

        formats = []
        formitaeten = try_get(video, lambda x: x['document']['formitaeten'], list)
        document = formitaeten and video['document']
        if formitaeten:
            title = document['titel']
            content_id = document['basename']

            format_urls = set()
            for f in formitaeten or []:
                self._extract_format(content_id, formats, format_urls, f)
        self._sort_formats(formats)

        thumbnails = []
        teaser_bild = document.get('teaserBild')
        if isinstance(teaser_bild, dict):
            for thumbnail_key, thumbnail in teaser_bild.items():
                thumbnail_url = try_get(
                    thumbnail, lambda x: x['url'], compat_str)
                if thumbnail_url:
                    thumbnails.append({
                        'url': thumbnail_url,
                        'id': thumbnail_key,
                        'width': int_or_none(thumbnail.get('width')),
                        'height': int_or_none(thumbnail.get('height')),
                    })

        return {
            'id': content_id,
            'title': title,
            'description': document.get('beschreibung'),
            'duration': int_or_none(document.get('length')),
            'timestamp': unified_timestamp(document.get('date')) or unified_timestamp(
                try_get(video, lambda x: x['meta']['editorialDate'], compat_str)),
            'thumbnails': thumbnails,
            'subtitles': self._extract_subtitles(document),
            'formats': formats,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id, fatal=False)
        if webpage:
            player = self._extract_player(webpage, url, fatal=False)
            if player:
                return self._extract_regular(url, player, video_id)

        return self._extract_mobile(video_id)


class ZDFChannelIE(ZDFBaseIE):
    _VALID_URL = r'https?://www\.zdf\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.zdf.de/sport/das-aktuelle-sportstudio',
        'info_dict': {
            'id': 'das-aktuelle-sportstudio',
            'title': 'das aktuelle sportstudio',
        },
        'playlist_mincount': 18,
    }, {
        'url': 'https://www.zdf.de/dokumentation/planet-e',
        'info_dict': {
            'id': 'planet-e',
            'title': 'planet e.',
        },
        'playlist_mincount': 50,
    }, {
        'url': 'https://www.zdf.de/gesellschaft/aktenzeichen-xy-ungeloest',
        'info_dict': {
            'id': 'aktenzeichen-xy-ungeloest',
            'title': 'Aktenzeichen XY... ungelöst',
            'entries': "lambda x: not any('xy580-fall1-kindermoerder-gesucht-100' in e['url'] for e in x)",
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://www.zdf.de/filme/taunuskrimi/',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if ZDFIE.suitable(url) else super(ZDFChannelIE, cls).suitable(url)

    def _og_search_title(self, webpage, fatal=False):
        title = super(ZDFChannelIE, self)._og_search_title(webpage, fatal=fatal)
        return re.split(r'\s+[-|]\s+ZDF(?:mediathek)?$', title or '')[0] or None

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        webpage = self._download_webpage(url, channel_id)

        matches = re.finditer(
            r'''<div\b[^>]*?\sdata-plusbar-id\s*=\s*(["'])(?P<p_id>[\w-]+)\1[^>]*?\sdata-plusbar-url=\1(?P<url>%s)\1''' % ZDFIE._VALID_URL,
            webpage)

        if self._downloader.params.get('noplaylist', False):
            entry = next(
                (self.url_result(m.group('url'), ie=ZDFIE.ie_key()) for m in matches),
                None)
            self.to_screen('Downloading just the main video because of --no-playlist')
            if entry:
                return entry
        else:
            self.to_screen('Downloading playlist %s - add --no-playlist to download just the main video' % (channel_id, ))

        def check_video(m):
            v_ref = self._search_regex(
                r'''(<a\b[^>]*?\shref\s*=[^>]+?\sdata-target-id\s*=\s*(["'])%s\2[^>]*>)''' % (m.group('p_id'), ),
                webpage, 'check id', default='')
            v_ref = extract_attributes(v_ref)
            return v_ref.get('data-target-video-type') != 'novideo'

        return self.playlist_from_matches(
            (m.group('url') for m in matches if check_video(m)),
            channel_id, self._og_search_title(webpage, fatal=False))
