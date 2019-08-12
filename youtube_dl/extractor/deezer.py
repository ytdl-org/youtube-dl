from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    orderedSet,
)


class DeezerPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?deezer\.com/playlist/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.deezer.com/playlist/176747451',
        'info_dict': {
            'id': '176747451',
            'title': 'Best!',
            'uploader': 'anonymous',
            'thumbnail': r're:^https?://e-cdns-images\.dzcdn\.net/images/cover/.*\.jpg$',
        },
        'playlist_count': 29,
    }

    def _real_extract(self, url):
        if 'test' not in self._downloader.params:
            self._downloader.report_warning('For now, this extractor only supports the 30 second previews. Patches welcome!')

        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)
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

        playlist_title = data['DATA']['TITLE']
        playlist_uploader = data['DATA']['PARENT_USERNAME']
        playlist_thumbnail = self._search_regex(
            r'<img id="naboo_playlist_image".*?src="([^"]+)"', webpage,
            'playlist thumbnail')

        entries = []
        for s in data['SONGS']['data']:
            formats = [{
                'format_id': 'preview',
                'url': s['MEDIA'][0]['HREF'],
                'preference': -100,  # Only the first 30 seconds
                'ext': 'mp3',
            }]
            self._sort_formats(formats)
            artists = ', '.join(
                orderedSet(a['ART_NAME'] for a in s['ARTISTS']))
            entries.append({
                'id': s['SNG_ID'],
                'duration': int_or_none(s.get('DURATION')),
                'title': '%s - %s' % (artists, s['SNG_TITLE']),
                'uploader': s['ART_NAME'],
                'uploader_id': s['ART_ID'],
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
