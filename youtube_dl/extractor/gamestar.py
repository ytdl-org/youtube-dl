# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor

class GameStarIE(InfoExtractor):
    _VALID_URL = r'http://www\.gamestar\.de/videos/.*,(?P<id>[0-9]+)\.html'
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
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        og_title = self._og_search_title(webpage)
        title = og_title.replace(' - Video bei GameStar.de', '').strip()

        url = 'http://gamestar.de/_misc/videos/portal/getVideoUrl.cfm?premium=0&videoId=' + video_id

        description = self._og_search_description(webpage).strip()

        og_thumbnail = self._og_search_thumbnail(webpage)
        thumbnail = 'http:' + og_thumbnail

        upload_date_raw = self._html_search_regex(
            r'<span style="float:left;font-size:11px;">Datum: ([0-9]+\.[0-9]+\.[0-9]+)&nbsp;&nbsp;',
            webpage, 'upload_date').split('.')
        upload_date = upload_date_raw[2] + upload_date_raw[1] + upload_date_raw[0]

        duration_raw = self._html_search_regex(
            r'&nbsp;&nbsp;Länge: ([0-9]+:[0-9]+)</span>', webpage, 'duration').split(':')
        duration = int(duration_raw[0])*60 + int(duration_raw[1])

        view_count_raw = self._html_search_regex(
            r'&nbsp;&nbsp;Zuschauer: ([0-9\.]+)&nbsp;&nbsp;', webpage, 'view_count')
        view_count = int(view_count_raw.replace('.', ''))

        comment_count_raw = self._html_search_regex(
            r'>Kommentieren \(([0-9]+)\)</a>', webpage, 'comment_count')
        comment_count = int(comment_count_raw)

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
