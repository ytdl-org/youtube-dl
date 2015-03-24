# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    float_or_none,
)


class RteIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?rte\.ie/player/[^/]{2,3}/show/(?P<id>[0-9]+)/'
    _TEST = {
        'url': 'http://www.rte.ie/player/de/show/10363114/',
        'info_dict': {
            'id': '10363114',
            'ext': 'mp4',
            'title': 'One News',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'The One O\'Clock News followed by Weather.',
            'duration': 436.844,
        },
        'params': {
            'skip_download': 'f4m fails with --test atm'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)
        description = self._html_search_meta('description', webpage, 'description')
        duration = float_or_none(self._html_search_meta(
            'duration', webpage, 'duration', fatal=False), 1000)

        thumbnail_id = self._search_regex(
            r'<meta name="thumbnail" content="uri:irus:(.*?)" />', webpage, 'thumbnail')
        thumbnail = 'http://img.rasset.ie/' + thumbnail_id + '.jpg'

        feeds_url = self._html_search_meta("feeds-prefix", webpage, 'feeds url') + video_id
        json_string = self._download_json(feeds_url, video_id)

        # f4m_url = server + relative_url
        f4m_url = json_string['shows'][0]['media:group'][0]['rte:server'] + json_string['shows'][0]['media:group'][0]['url']
        f4m_formats = self._extract_f4m_formats(f4m_url, video_id)
        f4m_formats = [{
            'format_id': f['format_id'],
            'url': f['url'],
            'ext': 'mp4',
            'width': f['width'],
            'height': f['height'],
        } for f in f4m_formats]

        return {
            'id': video_id,
            'title': title,
            'formats': f4m_formats,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
        }
