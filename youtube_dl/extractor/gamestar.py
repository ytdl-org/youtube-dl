# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    parse_duration,
    str_to_int,
    unified_strdate,
)


class GameStarIE(InfoExtractor):
    _VALID_URL = r'https?://www\.gamestar\.de/videos/.*,(?P<id>[0-9]+)\.html'
    _TEST = {
        'url': 'http://www.gamestar.de/videos/trailer,3/hobbit-3-die-schlacht-der-fuenf-heere,76110.html',
        'md5': '96974ecbb7fd8d0d20fca5a00810cea7',
        'info_dict': {
            'id': '76110',
            'ext': 'mp4',
            'title': 'Hobbit 3: Die Schlacht der Fünf Heere - Teaser-Trailer zum dritten Teil',
            'description': 'Der Teaser-Trailer zu Hobbit 3: Die Schlacht der Fünf Heere zeigt einige Szenen aus dem dritten Teil der Saga und kündigt den vollständigen Trailer an.',
            'thumbnail': 'http://images.gamestar.de/images/idgwpgsgp/bdb/2494525/600x.jpg',
            'upload_date': '20140728',
            'duration': 17
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        og_title = self._og_search_title(webpage)
        title = re.sub(r'\s*- Video (bei|-) GameStar\.de$', '', og_title)

        url = 'http://gamestar.de/_misc/videos/portal/getVideoUrl.cfm?premium=0&videoId=' + video_id

        description = self._og_search_description(webpage).strip()

        thumbnail = self._proto_relative_url(
            self._og_search_thumbnail(webpage), scheme='http:')

        upload_date = unified_strdate(self._html_search_regex(
            r'<span style="float:left;font-size:11px;">Datum: ([0-9]+\.[0-9]+\.[0-9]+)&nbsp;&nbsp;',
            webpage, 'upload_date', fatal=False))

        duration = parse_duration(self._html_search_regex(
            r'&nbsp;&nbsp;Länge: ([0-9]+:[0-9]+)</span>', webpage, 'duration',
            fatal=False))

        view_count = str_to_int(self._html_search_regex(
            r'&nbsp;&nbsp;Zuschauer: ([0-9\.]+)&nbsp;&nbsp;', webpage,
            'view_count', fatal=False))

        comment_count = int_or_none(self._html_search_regex(
            r'>Kommentieren \(([0-9]+)\)</a>', webpage, 'comment_count',
            fatal=False))

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'description': description,
            'upload_date': upload_date,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count
        }
