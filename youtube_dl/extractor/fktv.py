from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    determine_ext,
    js_to_json,
)


class FKTVIE(InfoExtractor):
    IE_NAME = 'fernsehkritik.tv'
    _VALID_URL = r'https?://(?:www\.)?fernsehkritik\.tv/folge-(?P<id>[0-9]+)(?:/.*)?'

    _TEST = {
        'url': 'http://fernsehkritik.tv/folge-1',
        'md5': '21f0b0c99bce7d5b524eb1b17b1c6d79',
        'info_dict': {
            'id': '1',
            'ext': 'mp4',
            'title': 'Folge 1 vom 10. April 2007',
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        episode = self._match_id(url)

        webpage = self._download_webpage(
            'http://fernsehkritik.tv/folge-%s/play' % episode, episode)
        title = clean_html(self._html_search_regex(
            '<h3>([^<]+)</h3>', webpage, 'title'))
        thumbnail = self._search_regex(r'POSTER\s*=\s*"([^"]+)', webpage, 'thumbnail', fatal=False)
        sources = self._parse_json(self._search_regex(r'(?s)MEDIA\s*=\s*(\[.+?\]);', webpage, 'media'), episode, js_to_json)

        formats = []
        for source in sources:
            furl = source.get('src')
            if furl:
                formats.append({
                    'url': furl,
                    'format_id': determine_ext(furl),
                })
        self._sort_formats(formats)

        return {
            'id': episode,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
        }
