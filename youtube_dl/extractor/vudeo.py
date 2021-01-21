# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VudeoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vudeo\.net/(?P<id>\w+).html'
    _TEST = {
        'url': 'https://vudeo.net/y4hycwg4ldgt.html',
        'md5': 'd9fb488c87d359810495f1f64342c404',
        'info_dict': {
            'id': 'y4hycwg4ldgt',
            'ext': 'mp4',
            'title': 'Poissonsexe 2020 FRENCH 720p WEB x264 PREUMS Extreme Down Video',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>Watch\s*(.+?)</title>', webpage, 'title')

        sources = self._parse_json(
            '[{}]'.format(
                self._html_search_regex(
                    r'sources:[\n\s]*\[(.*)\]',
                    webpage,
                    'sources'
                )
            ),
            video_id
        )

        return {
            'id': video_id,
            'title': title,
            'formats': [
                {'url': source}
                for source in sources
            ]
        }
