# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_filesize


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de/multimedia/(?:sendung/ts|video/video)(?P<id>-?[0-9]+)\.html'

    _TESTS = [{
        'url': 'http://www.tagesschau.de/multimedia/video/video1399128.html',
        'md5': 'bcdeac2194fb296d599ce7929dfa4009',
        'info_dict': {
            'id': '1399128',
            'ext': 'mp4',
            'title': 'Harald Range, Generalbundesanwalt, zu den Ermittlungen',
            'description': 'md5:69da3c61275b426426d711bde96463ab',
            'thumbnail': 're:^http:.*\.jpg$',
        },
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/ts-5727.html',
        'md5': '3c54c1f6243d279b706bde660ceec633',
        'info_dict': {
            'id': '5727',
            'ext': 'mp4',
            'description': 'md5:695c01bfd98b7e313c501386327aea59',
            'title': 'Sendung: tagesschau \t04.12.2014 20:00 Uhr',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }]

    _FORMATS = {
        's': {'width': 256, 'height': 144, 'quality': 1},
        'm': {'width': 512, 'height': 288, 'quality': 2},
        'l': {'width': 960, 'height': 544, 'quality': 3},
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        display_id = video_id.lstrip('-')
        webpage = self._download_webpage(url, display_id)

        player_url = self._html_search_meta(
            'twitter:player', webpage, 'player URL', default=None)
        if player_url:
            playerpage = self._download_webpage(
                player_url, display_id, 'Downloading player page')

            medias = re.findall(
                r'"(http://media.+?)", type:"video/(.+?)", quality:"(.+?)"',
                playerpage)
            formats = []
            for url, ext, res in medias:
                f = {
                    'format_id': res + '_' + ext,
                    'url': url,
                    'ext': ext,
                }
                f.update(self._FORMATS.get(res, {}))
                formats.append(f)
            thumbnail_fn = re.findall(r'"(/multimedia/.+?\.jpg)"', playerpage)[-1]
            title = self._og_search_title(webpage).strip()
            description = self._og_search_description(webpage).strip()
        else:
            download_text = self._search_regex(
                r'(?s)<p>Wir bieten dieses Video in folgenden Formaten zum Download an:</p>\s*<div class="controls">(.*?)</div>\s*<p>',
                webpage, 'download links')
            links = re.finditer(
                r'<div class="button" title="(?P<title>[^"]*)"><a href="(?P<url>[^"]+)">(?P<name>.+?)</a></div>',
                download_text)
            formats = []
            for l in links:
                format_id = self._search_regex(
                    r'.*/[^/.]+\.([^/]+)\.[^/.]+', l.group('url'), 'format ID')
                format = {
                    'format_id': format_id,
                    'url': l.group('url'),
                    'format_name': l.group('name'),
                }
                m = re.match(
                    r'''(?x)
                        Video:\s*(?P<vcodec>[a-zA-Z0-9/._-]+)\s*&\#10;
                        (?P<width>[0-9]+)x(?P<height>[0-9]+)px&\#10;
                        (?P<vbr>[0-9]+)kbps&\#10;
                        Audio:\s*(?P<abr>[0-9]+)kbps,\s*(?P<audio_desc>[A-Za-z\.0-9]+)&\#10;
                        Gr&ouml;&szlig;e:\s*(?P<filesize_approx>[0-9.,]+\s+[a-zA-Z]*B)''',
                    l.group('title'))
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
                formats.append(format)
            thumbnail_fn = self._search_regex(
                r'(?s)<img alt="Sendungsbild".*?src="([^"]+)"',
                webpage, 'thumbnail', fatal=False)
            description = self._html_search_regex(
                r'(?s)<p class="teasertext">(.*?)</p>',
                webpage, 'description', fatal=False)
            title = self._html_search_regex(
                r'<span class="headline".*?>(.*?)</span>', webpage, 'title')

        self._sort_formats(formats)
        thumbnail = 'http://www.tagesschau.de' + thumbnail_fn

        return {
            'id': display_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
            'description': description,
        }
