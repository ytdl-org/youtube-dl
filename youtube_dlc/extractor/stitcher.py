from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    js_to_json,
    unescapeHTML,
)


class StitcherIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?stitcher\.com/podcast/(?:[^/]+/)+e/(?:(?P<display_id>[^/#?&]+?)-)?(?P<id>\d+)(?:[/#?&]|$)'
    _TESTS = [{
        'url': 'http://www.stitcher.com/podcast/the-talking-machines/e/40789481?autoplay=true',
        'md5': '391dd4e021e6edeb7b8e68fbf2e9e940',
        'info_dict': {
            'id': '40789481',
            'ext': 'mp3',
            'title': 'Machine Learning Mastery and Cancer Clusters',
            'description': 'md5:55163197a44e915a14a1ac3a1de0f2d3',
            'duration': 1604,
            'thumbnail': r're:^https?://.*\.jpg',
        },
    }, {
        'url': 'http://www.stitcher.com/podcast/panoply/vulture-tv/e/the-rare-hourlong-comedy-plus-40846275?autoplay=true',
        'info_dict': {
            'id': '40846275',
            'display_id': 'the-rare-hourlong-comedy-plus',
            'ext': 'mp3',
            'title': "The CW's 'Crazy Ex-Girlfriend'",
            'description': 'md5:04f1e2f98eb3f5cbb094cea0f9e19b17',
            'duration': 2235,
            'thumbnail': r're:^https?://.*\.jpg',
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # escaped title
        'url': 'http://www.stitcher.com/podcast/marketplace-on-stitcher/e/40910226?autoplay=true',
        'only_matching': True,
    }, {
        'url': 'http://www.stitcher.com/podcast/panoply/getting-in/e/episode-2a-how-many-extracurriculars-should-i-have-40876278?autoplay=true',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        audio_id = mobj.group('id')
        display_id = mobj.group('display_id') or audio_id

        webpage = self._download_webpage(url, display_id)

        episode = self._parse_json(
            js_to_json(self._search_regex(
                r'(?s)var\s+stitcher(?:Config)?\s*=\s*({.+?});\n', webpage, 'episode config')),
            display_id)['config']['episode']

        title = unescapeHTML(episode['title'])
        formats = [{
            'url': episode[episode_key],
            'ext': determine_ext(episode[episode_key]) or 'mp3',
            'vcodec': 'none',
        } for episode_key in ('episodeURL',) if episode.get(episode_key)]
        description = self._search_regex(
            r'Episode Info:\s*</span>([^<]+)<', webpage, 'description', fatal=False)
        duration = int_or_none(episode.get('duration'))
        thumbnail = episode.get('episodeImage')

        return {
            'id': audio_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'formats': formats,
        }
