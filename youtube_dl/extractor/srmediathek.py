# encoding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import js_to_json


class SRMediathekIE(InfoExtractor):
    IE_DESC = 'Saarländischer Rundfunk'
    _VALID_URL = r'https?://sr-mediathek\.sr-online\.de/index\.php\?.*?&id=(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://sr-mediathek.sr-online.de/index.php?seite=7&id=28455',
        'info_dict': {
            'id': '28455',
            'ext': 'mp4',
            'title': 'sportarena (26.10.2014)',
            'description': 'Ringen: KSV Köllerbach gegen Aachen-Walheim; Frauen-Fußball: 1. FC Saarbrücken gegen Sindelfingen; Motorsport: Rallye in Losheim; dazu: Interview mit Timo Bernhard; Turnen: TG Saar; Reitsport: Deutscher Voltigier-Pokal; Badminton: Interview mit Michael Fuchs ',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        murls = json.loads(js_to_json(self._search_regex(
            r'var mediaURLs\s*=\s*(.*?);\n', webpage, 'video URLs')))
        formats = [{'url': murl} for murl in murls]
        self._sort_formats(formats)

        title = json.loads(js_to_json(self._search_regex(
            r'var mediaTitles\s*=\s*(.*?);\n', webpage, 'title')))[0]

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }
