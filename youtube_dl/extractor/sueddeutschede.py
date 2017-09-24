# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)


class SueddeutscheDeIE(InfoExtractor):
    _VALID_URL = r'https?://www\.sueddeutsche\.de/[^/]+/[^/]+-(?P<id>1\.\d+)'
    _TEST = {
        'url': 'http://www.sueddeutsche.de/auto/marodes-schienennetz-die-politik-dreht-sich-viel-zu-sehr-um-den-strassenverkehr-ein-kommentar-1.3639046',
        'md5': '0da13bf4f8d5ac4aac1de70632adf909',
        'info_dict': {
            'id': '1.3639046',
            'ext': 'mp4',
            'title': 'Abgesenkte Gleise bei der Rheintalbahn legen Zugverkehr lahm',
            'description': 'Seit elf Tagen steht der Schienen-Güterverkehr auf der Rheintalbahn zwischen Nord und Süd still. Grund ist eine Tunnelbaustelle bei Rastatt, die zum Desaster wurde. ',
            'timestamp': 1503563773,
            'upload_date': '20170824',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        meta = self._parse_json(self._search_regex(
            r'var video = (\{.*?\});', webpage, 'video parameters'), video_id)

        return {
            'id': video_id,
            'title': meta['title'],
            'url': meta['videoUrl'],
            'thumbnail': meta.get('posterUrl'),
            'description': meta.get('description'),
            'timestamp': parse_iso8601(meta.get('pubdateFull')),
            'duration': parse_duration(meta.get('durationInSeconds')),
        }
