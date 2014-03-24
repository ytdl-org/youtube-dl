# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    parse_iso8601,
    unescapeHTML,
)


class RTSIE(InfoExtractor):
    IE_DESC = 'RTS.ch'
    _VALID_URL = r'^https?://(?:www\.)?rts\.ch/archives/tv/[^/]+/(?P<id>[0-9]+)-.*?\.html'

    _TEST = {
        'url': 'http://www.rts.ch/archives/tv/divers/3449373-les-enfants-terribles.html',
        'md5': '753b877968ad8afaeddccc374d4256a5',
        'info_dict': {
            'id': '3449373',
            'ext': 'mp4',
            'duration': 1488,
            'title': 'Les Enfants Terribles',
            'description': 'France Pommier et sa soeur Luce Feral, les deux filles de ce groupe de 5.',
            'uploader': 'Divers',
            'upload_date': '19680921',
            'timestamp': -40280400,
            'thumbnail': 're:^https?://.*\.image'
        },
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        all_info = self._download_json(
            'http://www.rts.ch/a/%s.html?f=json/article' % video_id, video_id)
        info = all_info['video']['JSONinfo']

        upload_timestamp = parse_iso8601(info.get('broadcast_date'))
        duration = parse_duration(info.get('duration'))
        thumbnail = unescapeHTML(info.get('preview_image_url'))
        formats = [{
            'format_id': fid,
            'url': furl,
            'tbr': int_or_none(self._search_regex(
                r'-([0-9]+)k\.', furl, 'bitrate', default=None)),
        } for fid, furl in info['streams'].items()]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': info['title'],
            'description': info.get('intro'),
            'duration': duration,
            'uploader': info.get('programName'),
            'timestamp': upload_timestamp,
            'thumbnail': thumbnail,
        }
