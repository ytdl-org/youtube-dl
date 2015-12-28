# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    js_to_json,
)


class ScreencastOMaticIE(InfoExtractor):
    _VALID_URL = r'https?://screencast-o-matic\.com/watch/(?P<id>[0-9a-zA-Z]+)'
    _TEST = {
        'url': 'http://screencast-o-matic.com/watch/c2lD3BeOPl',
        'md5': '483583cb80d92588f15ccbedd90f0c18',
        'info_dict': {
            'id': 'c2lD3BeOPl',
            'ext': 'mp4',
            'title': 'Welcome to 3-4 Philosophy @ DECV!',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'as the title says! also: some general info re 1) VCE philosophy and 2) distance learning.',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        setup_js = self._search_regex(
            r"(?s)jwplayer\('mp4Player'\).setup\((\{.*?\})\);",
            webpage, 'setup code')
        data = self._parse_json(setup_js, video_id, transform_source=js_to_json)
        try:
            video_data = next(
                m for m in data['modes'] if m.get('type') == 'html5')
        except StopIteration:
            raise ExtractorError('Could not find any video entries!')
        video_url = compat_urlparse.urljoin(url, video_data['config']['file'])
        thumbnail = data.get('image')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'url': video_url,
            'ext': 'mp4',
            'thumbnail': thumbnail,
        }
