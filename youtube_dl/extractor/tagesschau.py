# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    bool_or_none,
    compat_str,
    determine_ext,
    ExtractorError,
    parse_duration,
    parse_filesize,
    remove_quotes,
    strip_or_none,
    try_get,
    unescapeHTML,
    unified_timestamp,
    url_or_none,
)

# Note that there are tagesschau.de/api and tagesschau.de/api2 endpoints, which
# may be useful, but not all pages and not all formats can be easily accessed
# by API.


_FORMATS = {
    'xs': {'quality': 0},
    's': {'width': 320, 'height': 180, 'quality': 1},
    'sm': {'width': 480, 'height': 270, 'quality': 1},
    'm': {'width': 512, 'height': 288, 'quality': 2},
    'ml': {'width': 640, 'height': 360, 'quality': 2},
    'l': {'width': 960, 'height': 540, 'quality': 3},
    'xl': {'width': 1280, 'height': 720, 'quality': 4},
    'xxl': {'quality': 5},
    'mp3': {'abr': 64, 'vcodec': 'none', 'quality': 0},
    'hi.mp3': {'abr': 192, 'vcodec': 'none', 'quality': 1},
}

_FIELD_PREFERENCE = ('height', 'width', 'vbr', 'abr')


def _normalize_format_id(format_id, ext):
    if format_id:
        m = re.match(r"web([^.]+)\.[^.]+$", format_id)
        if m:
            format_id = m.group(1)
        if format_id == 'hi' and ext:
            # high-quality audio files
            format_id = '%s.%s' % (format_id, ext)
    return format_id


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de(?:/?|/(?P<path>[^?#]+?(?:/(?P<id>[^/#?]+?(?:-?[0-9]+))(?:~_?[^/#?]+?)?(?:\.html)?)?))(?:[#?].*)?$'

    _TESTS = [{
        'url': 'http://www.tagesschau.de/multimedia/video/video-102143.html',
        'md5': 'f7c27a0eff3bfe8c7727e65f8fe1b1e6',
        'info_dict': {
            'id': 'video-102143',
            'ext': 'mp4',
            'title': 'Regierungsumbildung in Athen: Neue Minister in Griechenland vereidigt',
            'description': '18.07.2015 20:10',
            'thumbnail': r're:^https?:.*\.jpg$',
            'upload_date': '20150718',
            'duration': 138,
            'timestamp': 1437250200,
            'uploader': 'ARD',
        },
    }, {
        # with player
        'url': 'http://www.tagesschau.de/multimedia/video/video-102143~player.html',
        'md5': 'f7c27a0eff3bfe8c7727e65f8fe1b1e6',
        'info_dict': {
            'id': 'video-102143',
            'ext': 'mp4',
            'title': 'Regierungsumbildung in Athen: Neue Minister in Griechenland vereidigt',
            'description': '18.07.2015 20:10',
            'thumbnail': r're:^https?:.*\.jpg$',
            'upload_date': '20150718',
            'timestamp': 1437250200,
            'uploader': 'ARD',
        },
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/ts-5727.html',
        'md5': '3c54c1f6243d279b706bde660ceec633',
        'info_dict': {
            'id': 'video-45741',
            'ext': 'mp4',
            'title': 'tagesschau 20 Uhr - 04.12.14 20:00',
            'description': '04.12.2014 20:00',
            'thumbnail': r're:^https?:.*\.jpg$',
            'uploader': 'tagesschau',
            'timestamp': 1417723200,
            'upload_date': '20141204',
            'subtitles': dict,
        },
    }, {
        # exclusive audio
        'url': 'https://www.tagesschau.de/multimedia/audio/audio-103205.html',
        'md5': 'c8e7b72aeca664031db0ba198519b09a',
        'info_dict': {
            'id': 'audio-103205',
            'ext': 'mp3',
            'title': 'Die USA: ein Impfwunder?',
            'description': '06.03.2021 06:07',
            'timestamp': 1615010820,
            'upload_date': '20210306',
            'thumbnail': r're:^https?:.*\.jpg$',
            'uploader': 'Jule Käppel, ARD Washington',
            'creator': 'ARD',
            'channel': 'tagesschau.de',
            'is_live': False,
        },
    }, {
        # audio in article
        'url': 'https://www.tagesschau.de/ausland/amerika/biden-versoehnung-101.html',
        'md5': '4c46b0283719d97aa976037e1ecb7b73',
        'info_dict': {
            'id': 'audio-103429',
            'title': 'Bidens Versöhnungswerk kommt nicht voran',
            'ext': 'mp3',
            'timestamp': 1615444860,
            'uploader': 'Sebastian Hesse, ARD Washington',
            'description': '11.03.2021 06:41',
            'upload_date': '20210311',
            'creator': 'ARD',
            'channel': 'tagesschau.de',
        },
    }, {
        # playlist in article
        'url': 'https://www.tagesschau.de/ausland/impfungen-coronavirus-usa-101.html',
        'info_dict': {
            'id': 'impfungen-coronavirus-usa-101',
            'title': 'Kampf gegen das Coronavirus: Impfwunder USA?',
        },
        'playlist_count': 2,
    }, {
        # article without videos
        'url': 'https://www.tagesschau.de/wirtschaft/ukraine-russland-kredit-101.html',
        'info_dict': {
            'id': 'ukraine-russland-kredit-101',
            'title': 'Ukraine stoppt Rückzahlung russischer Kredite',
        },
        'playlist_count': 0,
    }, {
        # legacy website
        'url': 'https://www.tagesschau.de/multimedia/video/video-102303~_bab-sendung-211.html',
        'md5': 'ab6d190c8147560d6429a467566affe6',
        'info_dict': {
            'id': 'video-102303',
            'ext': 'mp4',
            'title': 'Bericht aus Berlin: Sommerinterview mit Angela Merkel',
            'description': '19.07.2015 19:05 Uhr',
        }
    }, {
        # handling of generic title
        'url': 'https://www.tagesschau.de/multimedia/video/video-835681.html',
        'info_dict': {
            'id': 'video-835681',
            'ext': 'mp4',
            'title': 'Tagesschau in 100 Sekunden - 13.03.21 17:35',
            'upload_date': '20210313',
            'uploader': 'Tagesschau24',
            'description': '13.03.2021 17:35',
            'timestamp': 1615656900,
        }
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/tsg-3771.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/tt-3827.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/nm-3475.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/weltspiegel-3167.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/tsvorzwanzig-959.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/bab/bab-3299~_bab-sendung-209.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/multimedia/video/video-102303~_bab-sendung-211.html',
        'only_matching': True,
    }, {
        'url': 'http://www.tagesschau.de/100sekunden/index.html',
        'only_matching': True,
    }, {
        # playlist article with collapsing sections
        'url': 'http://www.tagesschau.de/wirtschaft/faq-freihandelszone-eu-usa-101.html',
        'only_matching': True,
    }, {
        'url': 'https://www.tagesschau.de/',
        'only_matching': True,
    }]

    def _video_id_from_url(self, url):
        if url:
            mobj = re.match(self._VALID_URL, url)
            if mobj:
                return mobj.group('id')

    def _handle_generic_titles(self, title, pixelConf):
        if strip_or_none(title, '').lower() not in ('ganze sendung', '100 sekunden',
                                                    'tagesschau in 100 sekunden'):
            return title
        # otherwise find more meaningful title than the generic Ganze Sendung/100 Sekunden
        for item in pixelConf:
            if item.get('tracker') == 'AGFdebug':
                s = try_get(item, lambda x: x['clipData']['program'], compat_str)
                if s:
                    # extract date and time
                    parts = (try_get(item, lambda x: x['clipData']['title'], compat_str)
                             or '').split('_')[-2:]
                    if len(parts) == 2:
                        title = "%s - %s" % (s, ' '.join(parts))
                    else:
                        title = s
                break
        return title

    def _extract_from_player(self, player_div, video_id_fallback, title_fallback):
        player_data = unescapeHTML(self._search_regex(
            r'data-config=(?P<quote>["\'])(?P<data>[^"\']*)(?P=quote)',
            player_div, 'data-config', group='data'))

        meta = self._parse_json(player_data, video_id_fallback, fatal=False)
        mc = try_get(meta, lambda x: x['mc'], dict)
        if not mc:
            # fallback if parsing json fails, as tagesschau API sometimes sends
            # invalid json
            stream_hls = remove_quotes(self._search_regex(
                r'"http[^"]+?\.m3u8"', player_data, '.m3u8-url', group=0))
            formats = self._extract_m3u8_formats(stream_hls, video_id_fallback,
                                                 ext='mp4', m3u8_id='hls',
                                                 entry_protocol='m3u8_native')
            self._sort_formats(formats, field_preference=_FIELD_PREFERENCE)
            return {
                'id': video_id_fallback,
                'title': title_fallback,
                'formats': formats,
            }

        # this url is more permanent than the original link
        webpage_url = url_or_none(try_get(mc, lambda x: x['_sharing']['link']))

        video_id = self._video_id_from_url(webpage_url)
        duration = None
        pixelConf = try_get(meta, lambda x: x['pc']['_pixelConfig'], list) or []
        for item in pixelConf:
            video_id = (video_id or try_get(item,
                        [lambda x: x['playerID'],
                         lambda x: x['clipData']['playerId']], compat_str))
            duration = (duration or parse_duration(try_get(item,
                        [lambda x: x['clipData']['length'],
                         lambda x: x['clipData']['duration']])))
        if not video_id:
            video_id = video_id_fallback

        formats = []
        for elem in mc.get('_mediaArray', []):
            for d in elem.get('_mediaStreamArray', []):
                link_url = url_or_none(d.get('_stream'))
                if not link_url:
                    continue
                ext = determine_ext(link_url)
                if ext == "m3u8":
                    formats.extend(self._extract_m3u8_formats(
                        link_url, video_id_fallback, ext='mp4',
                        entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                elif ext == "f4m":
                    formats.extend(self._extract_f4m_formats(
                        link_url, video_id_fallback, f4m_id='hds', fatal=False))
                else:
                    format_id = _normalize_format_id(self._search_regex(
                        r'.*/[^/.]+\.([^/]+)\.[^/.]+$', link_url, 'format ID',
                        default=ext, fatal=False),
                        ext)
                    fmt = {
                        'format_id': format_id,
                        'url': link_url,
                        'format_name': ext,
                    }
                    fmt.update(_FORMATS.get(format_id, {}))
                    formats.append(fmt)
        self._sort_formats(formats, field_preference=_FIELD_PREFERENCE)
        if not formats:
            raise ExtractorError("could not extract formats from json")

        # note that mc['_title'] can be very different from actual title,
        # such as an image description in case of audio files
        title = (try_get(mc, [lambda x: x['_info']['clipTitle'],
                              lambda x: x['_download']['title']], compat_str)
                 or title_fallback)
        title = self._handle_generic_titles(title, pixelConf)

        sub_url = url_or_none(mc.get('_subtitleUrl'))
        subs = {'de': [{'ext': 'ttml', 'url': sub_url}]} if sub_url else None

        images = try_get(mc, lambda x: x['_previewImage'], dict) or {}
        thumbnails = [{
            'url': url_or_none('https://www.tagesschau.de/%s'
                               % (images[format_id],)),
            'preference': _FORMATS.get(format_id, {}).get('quality'),
        } for format_id in images] or None

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'webpage_url': webpage_url,
            'subtitles': subs,
            'thumbnails': thumbnails,
            'duration': duration,
            'timestamp': unified_timestamp(try_get(mc, [lambda x: x['_download']['date'],
                                                        lambda x: x['_info']['clipDate']])),
            'is_live': bool_or_none(mc.get('_isLive')),
            'channel': try_get(mc, lambda x: x['_download']['channel'], compat_str),
            'uploader': try_get(mc, lambda x: x['_info']['channelTitle'], compat_str),
            'creator': try_get(mc, lambda x: x['_info']['clipContentSrc'], compat_str),
            'description': try_get(mc, lambda x: x['_info']['clipDate'], compat_str),
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('path')
        display_id = video_id.lstrip('-') if video_id else 'tagesschau.de'

        webpage = self._download_webpage(url, display_id)

        title = (self._og_search_title(webpage, default=None)
                 or self._html_search_regex(
                     [r'<span[^>]*class="headline"[^>]*>(.+?)</span>',
                      r'<title[^>]*>(.+?)</title>'],
                     webpage, 'title'))

        webpage_type = self._og_search_property('type', webpage, default=None)

        player_pattern = r'<div[^>]+data-ts_component=(?P<quote>["\'])ts-mediaplayer(?P=quote)[^>]*>'
        players = [m.group(0) for m in re.finditer(player_pattern, webpage)]
        if not players:
            # assume old website format
            return self._legacy_extract(webpage, display_id, title, webpage_type)
        elif (len(players) > 1
              and not self._downloader.params.get('noplaylist')
              and (webpage_type == 'website' or not mobj.group('id'))):
            # article or playlist
            entries = []
            seen = set()
            for player in players:
                entry = self._extract_from_player(player, video_id, title)
                if entry['id'] not in seen:
                    entries.append(entry)
                    seen.add(entry['id'])
            return self.playlist_result(entries, display_id, title)
        else:
            # single video/audio
            return self._extract_from_player(players[0], video_id, title)

    def _legacy_extract_formats(self, download_text, media_kind):
        links = re.finditer(
            r'<div class="button" title="(?P<title>[^"]*)"><a href="(?P<url>[^"]+)">(?P<name>.+?)</a></div>',
            download_text)
        formats = []
        for l in links:
            link_url = l.group('url')
            if not link_url:
                continue
            ext = determine_ext(link_url)
            format_id = _normalize_format_id(self._search_regex(
                r'.*/[^/.]+\.([^/]+)\.[^/.]+$', link_url, 'format ID',
                default=ext), ext)
            format = {
                'format_id': format_id,
                'url': l.group('url'),
                'format_name': l.group('name'),
            }
            title = l.group('title')
            if title:
                if media_kind.lower() == 'video':
                    m = re.match(
                        r'''(?x)
                            Video:\s*(?P<vcodec>[a-zA-Z0-9/._-]+)\s*&\#10;
                            (?P<width>[0-9]+)x(?P<height>[0-9]+)px&\#10;
                            (?P<vbr>[0-9]+)kbps&\#10;
                            Audio:\s*(?P<abr>[0-9]+)kbps,\s*(?P<audio_desc>[A-Za-z\.0-9]+)&\#10;
                            Gr&ouml;&szlig;e:\s*(?P<filesize_approx>[0-9.,]+\s+[a-zA-Z]*B)''',
                        title)
                    if m:
                        format.update({
                            'format_note': m.group('audio_desc'),
                            'vcodec': m.group('vcodec'),
                            'width': int(m.group('width')),
                            'height': int(m.group('height')),
                            'abr': int(m.group('abr')),
                            'vbr': int(m.group('vbr')),
                            'filesize_approx': parse_filesize(m.group('filesize_approx')),
                        })
                else:
                    m = re.match(
                        r'(?P<format>.+?)-Format\s*:\s*(?P<abr>\d+)kbps\s*,\s*(?P<note>.+)',
                        title)
                    if m:
                        format.update({
                            'format_note': '%s, %s' % (m.group('format'), m.group('note')),
                            'vcodec': 'none',
                            'abr': int(m.group('abr')),
                        })
            formats.append(format)
        self._sort_formats(formats)
        return formats

    # Some old pages still use the old format, so we keep the previous
    # extractor for now.
    def _legacy_extract(self, webpage, display_id, title, webpage_type):
        DOWNLOAD_REGEX = r'<p>Wir bieten dieses (?P<kind>Video|Audio) in folgenden Formaten zum Download an:</p>\s*<div class="controls">(?P<links>.*?)</div>\s*<p>'

        if webpage_type == 'website':  # Article
            entries = []
            for num, (entry_title, media_kind, download_text) in enumerate(re.findall(
                    r'<p[^>]+class="infotext"[^>]*>\s*(?:<a[^>]+>)?\s*<strong>(.+?)</strong>.*?</p>.*?%s' % DOWNLOAD_REGEX,
                    webpage, flags=re.S), 1):
                entries.append({
                    'id': '%s-%d' % (display_id, num),
                    'title': '%s' % entry_title,
                    'formats': self._legacy_extract_formats(download_text, media_kind),
                })
            if len(entries) != 1:
                return self.playlist_result(entries, display_id, title)
            formats = entries[0]['formats']
        else:  # Assume single video
            download_text = self._search_regex(
                DOWNLOAD_REGEX, webpage, 'download links', flags=re.S, group='links')
            media_kind = self._search_regex(
                DOWNLOAD_REGEX, webpage, 'media kind', default='Video', flags=re.S, group='kind')
            formats = self._legacy_extract_formats(download_text, media_kind)
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._html_search_regex(
            r'(?s)<p class="teasertext">(.*?)</p>',
            webpage, 'description', default=None)

        self._sort_formats(formats)

        return {
            'id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': description,
        }
