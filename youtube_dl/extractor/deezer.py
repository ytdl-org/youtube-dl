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
            'uploader': 'Anonymous',
            'thumbnail': 're:^https?://cdn-images.deezer.com/images/cover/.*\.jpg$',
        },
        'playlist_count': 30,
        'skip': 'Only available in .de',
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

        playlist_title = data.get('DATA', {}).get('TITLE')
        playlist_uploader = data.get('DATA', {}).get('PARENT_USERNAME')
        playlist_thumbnail = self._search_regex(
            r'<img id="naboo_playlist_image".*?src="([^"]+)"', webpage,
            'playlist thumbnail')

        preview_pattern = self._search_regex(
            r"var SOUND_PREVIEW_GATEWAY\s*=\s*'([^']+)';", webpage,
            'preview URL pattern', fatal=False)
        entries = []
        for s in data['SONGS']['data']:
            puid = s['MD5_ORIGIN']
            preview_video_url = preview_pattern.\
                replace('{0}', puid[0]).\
                replace('{1}', puid).\
                replace('{2}', s['MEDIA_VERSION'])
            formats = [{
                'format_id': 'preview',
                'url': preview_video_url,
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
