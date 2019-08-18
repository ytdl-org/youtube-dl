from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
)

class DeezerBaseInfoExtractor(InfoExtractor):

    def get_data(self, url):
        if 'test' not in self._downloader.params:
            self._downloader.report_warning('For now, this extractor only supports the 30 second previews. Patches welcome!')

        mobj = re.match(self._VALID_URL, url)
        id = mobj.group('id')

        webpage = self._download_webpage(url, id)
        geoblocking_msg = self._html_search_regex(
            r'<p class="soon-txt">(.*?)</p>', webpage, 'geoblocking message',
            default=None)
        if geoblocking_msg is not None:
            raise ExtractorError(
                'Deezer said: %s' % geoblocking_msg, expected=True)

        data_json = self._search_regex(
            (r'__DZR_APP_STATE__\s*=\s*({.+?})\s*</script>',
             r'naboo\.display\(\'[^\']+\',\s*(.*?)\);\n'),
            webpage, 'data JSON')
        data = json.loads(data_json)
        return id, webpage, data

class DeezerPlaylistIE(DeezerBaseInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?deezer\.com/(../)?playlist/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.deezer.com/playlist/176747451',
        'info_dict': {
            'id': '176747451',
            'title': 'Best!',
            'uploader': 'anonymous',
            'thumbnail': r're:^https?://(e-)?cdns-images\.dzcdn\.net/images/cover/.*\.jpg$',
        },
        'playlist_count': 29,
    }

    def _real_extract(self, url):
        playlist_id, webpage, data = self.get_data(url)

        playlist_title = data.get('DATA').get('TITLE')
        playlist_uploader = data.get('DATA').get('PARENT_USERNAME')
        playlist_thumbnail = self._search_regex(
            r'<img id="naboo_playlist_image".*?src="([^"]+)"', webpage,
            'playlist thumbnail')

        entries = []
        for s in data.get('SONGS').get('data'):
            formats = [{
                'format_id': 'preview',
                'url': s.get('MEDIA')[0].get('HREF'),
                'preference': -100,  # Only the first 30 seconds
                'ext': 'mp3',
            }]
            self._sort_formats(formats)
            artists = ', '.join(
                orderedSet(a.get('ART_NAME') for a in s.get('ARTISTS')))
            entries.append({
                'id': s.get('SNG_ID'),
                'duration': int_or_none(s.get('DURATION')),
                'title': '%s - %s' % (artists, s.get('SNG_TITLE')),
                'uploader': s.get('ART_NAME'),
                'uploader_id': s.get('ART_ID'),
                'age_limit': 16 if s.get('EXPLICIT_LYRICS') == '1' else 0,
                'formats': formats,
            })

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_title,
            'uploader': playlist_uploader,
            'thumbnail': playlist_thumbnail,
            'entries': entries,
        }
