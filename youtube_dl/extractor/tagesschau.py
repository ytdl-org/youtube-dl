# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import parse_filesize, ExtractorError


class TagesschauIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tagesschau\.de/multimedia/(?:sendung/(ts|tsg|tt|nm|bab/bab)|video/video|tsvorzwanzig)(?P<id>-?[0-9]+)(?:~[-_a-zA-Z0-9]*)?\.html'

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
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/tsg-3771.html',
        'md5': '90757268b49ef56deae90c7b48928d58',
        'info_dict': {
            'id': '3771',
            'ext': 'mp4',
            'description': None,
            'title': 'Sendung: tagesschau (mit Gebärdensprache) \t14.07.2015 20:00 Uhr',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/tt-3827.html',
        'md5': '6e3ebdc75e8d67da966a8d06721eda71',
        'info_dict': {
            'id': '3827',
            'ext': 'mp4',
            'description': 'md5:d511d0e278b0ad341a95ad9ab992ce66',
            'title': 'Sendung: tagesthemen \t14.07.2015 22:15 Uhr',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/nm-3475.html',
        'md5': '8a8875a568f0a5ae5ceef93c501a225f',
        'info_dict': {
            'id': '3475',
            'ext': 'mp4',
            'description': 'md5:ed149f5649cda3dac86813a9d777e131',
            'title': 'Sendung: nachtmagazin \t15.07.2015 00:15 Uhr',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }, {
        'url': 'http://www.tagesschau.de/multimedia/tsvorzwanzig-959.html',
        'md5': 'be4d6f0421f2acd8abe25ea29f6f015b',
        'info_dict': {
            'id': '959',
            'ext': 'mp4',
            'description': None,
            'title': 'Sendung: tagesschau vor 20 Jahren \t14.07.2015 22:45 Uhr',
            'thumbnail': 're:^http:.*\.jpg$',
        }
    }, {
        'url': 'http://www.tagesschau.de/multimedia/sendung/bab/bab-3299~_bab-sendung-209.html',
        'md5': '42e3757018d9908581481a80cc1806da',
        'info_dict': {
            'id': '3299',
            'ext': 'mp4',
            'description': None,
            'title': 'Nach dem Referendum: Schaltgespräch nach Athen',
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
            # there are some videos without description
            description = ""
            description = self._html_search_regex(
                r'(?s)<p class="teasertext">(.*?)</p>',
                webpage, 'description', fatal=False, default=None)
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
