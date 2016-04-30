# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    parse_filesize,
)


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de/[^/]+/(?:[^/]+/)*?[^/#?]+?(?P<id>-?[0-9]+)(?:~_?[^/#?]+?)?\.html'

    _TESTS = [{
        'url': 'http://www.tagesschau.de/multimedia/video/video-102143.html',
        'md5': 'f7c27a0eff3bfe8c7727e65f8fe1b1e6',
        'info_dict': {
            'id': '102143',
            'ext': 'mp4',
            'title': 'Regierungsumbildung in Athen: Neue Minister in Griechenland vereidigt',
            'description': 'md5:171feccd9d9b3dd54d05d501568f6359',
            'thumbnail': 're:^https?:.*\.jpg$',
        },
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/ts-5727.html',
        'md5': '3c54c1f6243d279b706bde660ceec633',
        'info_dict': {
            'id': '5727',
            'ext': 'mp4',
            'description': 'md5:695c01bfd98b7e313c501386327aea59',
            'title': 'Sendung: tagesschau \t04.12.2014 20:00 Uhr',
            'thumbnail': 're:^https?:.*\.jpg$',
        },
    }, {
        'url': 'http://www.tagesschau.de/multimedia/politikimradio/audio-18407.html',
        'md5': 'aef45de271c4bf0a5db834aa40bf774c',
        'info_dict': {
            'id': '18407',
            'ext': 'mp3',
            'title': 'Flüchtlingsdebatte: Hitzig, aber wenig hilfreich',
            'description': 'Flüchtlingsdebatte: Hitzig, aber wenig hilfreich',
            'thumbnail': 're:^https?:.*\.jpg$',
        },
    }, {
        'url': 'http://www.tagesschau.de/inland/afd-parteitag-135.html',
        'info_dict': {
            'id': '135',
            'title': 'Möchtegern-Underdog mit Machtanspruch',
        },
        'playlist_count': 2,
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
        'url': 'http://www.tagesschau.de/multimedia/video/video-179517~player.html',
        'only_matching': True,
    }]

    _FORMATS = {
        'xs': {'quality': 0},
        's': {'width': 320, 'height': 180, 'quality': 1},
        'm': {'width': 512, 'height': 288, 'quality': 2},
        'l': {'width': 960, 'height': 540, 'quality': 3},
        'xl': {'width': 1280, 'height': 720, 'quality': 4},
        'xxl': {'quality': 5},
    }

    def _extract_formats(self, download_text, media_kind):
        links = re.finditer(
            r'<div class="button" title="(?P<title>[^"]*)"><a href="(?P<url>[^"]+)">(?P<name>.+?)</a></div>',
            download_text)
        formats = []
        for l in links:
            link_url = l.group('url')
            if not link_url:
                continue
            format_id = self._search_regex(
                r'.*/[^/.]+\.([^/]+)\.[^/.]+$', link_url, 'format ID',
                default=determine_ext(link_url))
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

    def _real_extract(self, url):
        video_id = self._match_id(url)
        display_id = video_id.lstrip('-')
        webpage = self._download_webpage(url, display_id)

        player_url = self._html_search_meta(
            'twitter:player', webpage, 'player URL', default=None)
        if player_url:
            playerpage = self._download_webpage(
                player_url, display_id, 'Downloading player page')

            formats = []
            for media in re.finditer(
                    r'''(?x)
                        (?P<q_url>["\'])(?P<url>http://media.+?)(?P=q_url)
                        ,\s*type:(?P<q_type>["\'])(?P<type>video|audio)/(?P<ext>.+?)(?P=q_type)
                        (?:,\s*quality:(?P<q_quality>["\'])(?P<quality>.+?)(?P=q_quality))?
                    ''', playerpage):
                url = media.group('url')
                webpage_type = media.group('type')
                ext = media.group('ext')
                res = media.group('quality')
                f = {
                    'format_id': '%s_%s' % (res, ext) if res else ext,
                    'url': url,
                    'ext': ext,
                    'vcodec': 'none' if webpage_type == 'audio' else None,
                }
                f.update(self._FORMATS.get(res, {}))
                formats.append(f)
            thumbnail = self._og_search_thumbnail(playerpage)
            title = self._og_search_title(webpage).strip()
            description = self._og_search_description(webpage).strip()
        else:
            title = self._html_search_regex(
                r'<span class="headline".*?>(.*?)</span>', webpage, 'title')

            DOWNLOAD_REGEX = r'(?s)<p>Wir bieten dieses (?P<kind>Video|Audio) in folgenden Formaten zum Download an:</p>\s*<div class="controls">(?P<links>.*?)</div>\s*<p>'

            webpage_type = self._og_search_property('type', webpage, default=None)
            if webpage_type == 'website':  # Article
                entries = []
                for num, (entry_title, media_kind, download_text) in enumerate(re.findall(
                        r'(?s)<p[^>]+class="infotext"[^>]*>.*?<strong>(.+?)</strong>.*?</p>.*?%s' % DOWNLOAD_REGEX,
                        webpage)):
                    entries.append({
                        'id': display_id,
                        'title': '%s-%d' % (entry_title, num),
                        'formats': self._extract_formats(download_text, media_kind),
                    })
                return self.playlist_result(entries, display_id, title)
            else:  # Assume single video
                download_text = self._search_regex(
                    DOWNLOAD_REGEX, webpage, 'download links', group='links')
                media_kind = self._search_regex(
                    DOWNLOAD_REGEX, webpage, 'media kind', default='Video', group='links')
                formats = self._extract_formats(download_text, media_kind)
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
