# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    int_or_none,
    NO_DEFAULT,
    orderedSet,
    parse_codecs,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
    urljoin,
)


class ZDFIE(InfoExtractor):
    _VALID_URL = r'https?://www\.zdf\.de/(?:[^/]+/)*(?P<id>[^/?]+)\.html'
    _QUALITIES = ('auto', 'low', 'med', 'high', 'veryhigh')
    _GEO_COUNTRIES = ['DE']

    _TESTS = [{
        'url': 'https://www.zdf.de/dokumentation/terra-x/die-magie-der-farben-von-koenigspurpur-und-jeansblau-100.html',
        'info_dict': {
            'id': 'die-magie-der-farben-von-koenigspurpur-und-jeansblau-100',
            'ext': 'mp4',
            'title': 'Die Magie der Farben (2/2)',
            'description': 'md5:a89da10c928c6235401066b60a6d5c1a',
            'duration': 2615,
            'timestamp': 1465021200,
            'upload_date': '20160604',
        },
    }, {
        'url': 'https://www.zdf.de/dokumentation/terra-x/mit-antischwerkraft-zu-den-sternen-100.html',
        'md5': 'dede0475add7c2d1fa067358a636e80e',
        'info_dict': {
            'id': 'mit-antischwerkraft-zu-den-sternen-100',
            'ext': 'mp4',
            'title': 'Mit Antischwerkraft zu den Sternen?',
            'description': 'md5:44c0214d0bd2f41a5200af6b38e15186',
            'duration': 311,
            'timestamp': 1538294400,
            'upload_date': '20180930',
        }
    }, {
        'url': 'https://www.zdf.de/service-und-hilfe/die-neue-zdf-mediathek/zdfmediathek-trailer-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/filme/taunuskrimi/die-lebenden-und-die-toten-1---ein-taunuskrimi-100.html',
        'only_matching': True,
    }, {
        'url': 'https://www.zdf.de/dokumentation/planet-e/planet-e-uebersichtsseite-weitere-dokumentationen-von-planet-e-100.html',
        'only_matching': True,
    }]

    _MP4_URL_REGEX = r'^(?P<base_url>((https?:)?//)?(.*))_(?P<bitrate>[0-9]+)k_p(?P<p>[0-9]{1,})v(?P<v>[0-9]{1,})\.(?P<ext>.{2,3})$'

    _H264_MAIN_L31 = 'avc1.4d001f'
    _H264_HIGH_L4 = 'avc1.640028'

    # https://github.com/mediathekview/MServer/blob/master/src/main/java/mServer/crawler/sender/MediathekZdf.java
    _BITRATES = {
        11: {
            35: [{
                'tbr': 2328,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
        },
        12: {
            14: [{
                'tbr': 2256,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            15: [{
                'tbr': 3256,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }],
            35: [{
                'tbr': 2328,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            36: [{
                'tbr': 3328,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }],
        },
        13: {
            14: [{
                'tbr': 2296,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            15: [{
                'tbr': 3296,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }],
            35: [{
                'tbr': 2328,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            36: [{
                'tbr': 3328,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }],
        },
        14: {
            14: [{
                'tbr': 2296,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            35: [{
                'tbr': 3328,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }, {
                'tbr': 2328,
                'width': 1024,
                'height': 576,
                'vcodec': _H264_MAIN_L31,
            }],
            36: [{
                'tbr': 3328,
                'width': 1280,
                'height': 720,
                'vcodec': _H264_HIGH_L4,
            }],
        },
    }

    def _call_api(self, url, player, referrer, video_id, item):
        return self._download_json(
            url, video_id, 'Downloading JSON %s' % item,
            headers={
                'Referer': referrer,
                'Api-Auth': 'Bearer %s' % player['apiToken'],
            })

    def _extract_player(self, webpage, video_id, fatal=True):
        return self._parse_json(
            self._search_regex(
                r'(?s)data-zdfplayer-jsb=(["\'])(?P<json>{.+?})\1', webpage,
                'player JSON', default='{}' if not fatal else NO_DEFAULT,
                group='json'),
            video_id)

    def _get_max_bitrate(self, url):
        m = re.search(self._MP4_URL_REGEX, url)
        if m:
            return int_or_none(m.group('bitrate'))
        return None

    @staticmethod
    def _guess_resolution(bitrate):
        if bitrate < 400:
            return {'width': 320, 'height': 176}
        if 400 <= bitrate < 500:
            return {'width': 480, 'height': 272}
        if 500 <= bitrate < 1000:
            return {'width': 640, 'height': 360}
        if 1000 <= bitrate < 1500:
            return {'width': 852, 'height': 480}
        if 1500 <= bitrate < 2000:
            return {'width': 1024, 'height': 576}
        return {'width': 1280, 'height': 720}

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

    @staticmethod
    def _set_language(formats, lang):
        if not lang:
            return
        for format in formats:
            format['language'] = lang

    @staticmethod
    def _find_single_language(formats):
        first_lang = None
        for format in formats:
            lang = format.get('language')
            if lang and not first_lang:
                first_lang = lang
                continue
            if lang != first_lang:
                return
        return first_lang

    def _find_additional_formats(self, formats, video_id, lang=None):
        present = {}
        for format in formats:
            url = format.get('url')
            if not url:
                continue
            m = re.match(self._MP4_URL_REGEX, url)
            if not m:
                continue
            base_url = m.group('base_url')
            p = int_or_none(m.group('p'))
            v = int_or_none(m.group('v'))
            if not p or not v:
                continue
            if base_url not in present:
                present[base_url] = {v: [p]}
            elif v not in present[base_url]:
                present[base_url][v] = [p]
            elif p not in present[base_url][v]:
                present[base_url][v].append(p)

        for base_url, vs in present.items():
            for v, ps in vs.items():
                for p, variants in (x for x in self._BITRATES.get(v, {}).items() if x[0] not in ps):
                    for f in variants:
                        f = dict(f)
                        url = '%s_%sk_p%sv%s.mp4' % (base_url, f['tbr'], p, v)
                        if self._is_valid_url(url, video_id):
                            f.update({
                                'url': url,
                                'format_id': 'mp4-%s' % f['tbr'],
                                'ext': 'mp4',
                                'language': lang,
                                'acodec': 'mp4a.40.2',
                            })
                            if 'nrodlzdf' in url:
                                f['format_id'] += '-alt'
                                f['source_preference'] = -2
                            formats.append(f)

    def _extract_format(self, video_id, formats, format_urls, meta):
        format_url = url_or_none(meta.get('url'))
        if not format_url:
            return
        if format_url in format_urls:
            return
        format_urls.add(format_url)
        mime_type = meta.get('mimeType')
        ext = determine_ext(format_url)
        if mime_type == 'application/x-mpegURL' or ext == 'm3u8':
            hls_formats = self._extract_m3u8_formats(
                format_url, video_id, 'mp4', m3u8_id='hls',
                entry_protocol='m3u8_native', fatal=False)
            self._set_language(hls_formats, meta.get('language'))
            formats.extend(hls_formats)
        elif mime_type == 'application/f4m+xml' or ext == 'f4m':
            hds_formats = self._extract_f4m_formats(
                update_url_query(format_url, {'hdcore': '3.7.0'}),
                video_id, f4m_id='hds', fatal=False)
            self._set_language(hds_formats, meta.get('language'))
            formats.extend(hds_formats)
        else:
            f = parse_codecs(meta.get('mimeCodec'))
            bitrate = self._get_max_bitrate(format_url)
            format_note = meta.get('quality')
            f.update({
                'url': format_url,
                'format_id': 'mp4-%s' % bitrate or format_note or '0',
                'ext': ext,
                'tbr': bitrate,
                'language': meta.get('language'),
            })
            if not f.get('width') and not f.get('height') and bitrate:
                f.update(self._guess_resolution(bitrate))
            if 'nrodlzdf' in format_url:
                f['format_id'] += '-alt'
                f['source_preference'] = -2
            formats.append(f)

    def _extract_entry(self, url, player, content, video_id):
        title = content.get('title') or content['teaserHeadline']

        t = content['mainVideoContent']['http://zdf.de/rels/target']

        ptmd_path = t.get('http://zdf.de/rels/streams/ptmd')

        if not ptmd_path:
            ptmd_path = t[
                'http://zdf.de/rels/streams/ptmd-template'].replace(
                '{playerId}', 'portal')

        ptmd = self._call_api(
            urljoin(url, ptmd_path), player, url, video_id, 'metadata')

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
                            video_id, formats, track_uris, {
                                'url': track.get('uri'),
                                'type': f.get('type'),
                                'mimeType': f.get('mimeType'),
                                'mimeCodec': quality.get('mimeCodec'),
                                'quality': quality.get('quality'),
                                'language': track.get('language'),
                            })
        single_lang = self._find_single_language(formats)
        self._find_additional_formats(formats, video_id, single_lang)
        self._sort_formats(formats)

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

        return {
            'id': video_id,
            'title': title,
            'description': content.get('leadParagraph') or content.get('teasertext'),
            'duration': int_or_none(t.get('duration')),
            'timestamp': unified_timestamp(content.get('editorialDate')),
            'thumbnails': thumbnails,
            'subtitles': self._extract_subtitles(ptmd),
            'formats': formats,
        }

    def _extract_regular(self, url, player, video_id):
        content = self._call_api(
            player['content'], player, url, video_id, 'content')
        return self._extract_entry(player['content'], player, content, video_id)

    def _extract_mobile(self, video_id):
        document = self._download_json(
            'https://zdf-cdn.live.cellular.de/mediathekV2/document/%s' % video_id,
            video_id)['document']

        title = document['titel']

        formats = []
        format_urls = set()
        for f in document['formitaeten']:
            self._extract_format(video_id, formats, format_urls, f)
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
            'id': video_id,
            'title': title,
            'description': document.get('beschreibung'),
            'duration': int_or_none(document.get('length')),
            'timestamp': unified_timestamp(try_get(
                document, lambda x: x['meta']['editorialDate'], compat_str)),
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


class ZDFChannelIE(InfoExtractor):
    _VALID_URL = r'https?://www\.zdf\.de/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'https://www.zdf.de/sport/das-aktuelle-sportstudio',
        'info_dict': {
            'id': 'das-aktuelle-sportstudio',
            'title': 'das aktuelle sportstudio | ZDF',
        },
        'playlist_count': 21,
    }, {
        'url': 'https://www.zdf.de/dokumentation/planet-e',
        'info_dict': {
            'id': 'planet-e',
            'title': 'planet e.',
        },
        'playlist_count': 4,
    }, {
        'url': 'https://www.zdf.de/filme/taunuskrimi/',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        return False if ZDFIE.suitable(url) else super(ZDFChannelIE, cls).suitable(url)

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        webpage = self._download_webpage(url, channel_id)

        entries = [
            self.url_result(item_url, ie=ZDFIE.ie_key())
            for item_url in orderedSet(re.findall(
                r'data-plusbar-url=["\'](http.+?\.html)', webpage))]

        return self.playlist_result(
            entries, channel_id, self._og_search_title(webpage, fatal=False))
