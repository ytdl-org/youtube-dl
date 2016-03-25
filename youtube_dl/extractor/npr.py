from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlencode
from ..utils import (
    int_or_none,
    qualities,
)


class NprIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?npr\.org/player/v2/mediaPlayer\.html\?.*\bid=(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.npr.org/player/v2/mediaPlayer.html?id=449974205',
        'info_dict': {
            'id': '449974205',
            'title': 'New Music From Beach House, Chairlift, CMJ Discoveries And More'
        },
        'playlist_count': 7,
    }, {
        'url': 'http://www.npr.org/player/v2/mediaPlayer.html?action=1&t=1&islist=false&id=446928052&m=446929930&live=1',
        'info_dict': {
            'id': '446928052',
            'title': "Songs We Love: Tigran Hamasyan, 'Your Mercy is Boundless'"
        },
        'playlist': [{
            'md5': '12fa60cb2d3ed932f53609d4aeceabf1',
            'info_dict': {
                'id': '446929930',
                'ext': 'mp3',
                'title': 'Your Mercy is Boundless (Bazum en Qo gtutyunqd)',
                'duration': 402,
            },
        }],
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        config = self._download_json(
            'http://api.npr.org/query?%s' % compat_urllib_parse_urlencode({
                'id': playlist_id,
                'fields': 'titles,audio,show',
                'format': 'json',
                'apiKey': 'MDAzMzQ2MjAyMDEyMzk4MTU1MDg3ZmM3MQ010',
            }), playlist_id)

        story = config['list']['story'][0]

        KNOWN_FORMATS = ('threegp', 'mp4', 'mp3')
        quality = qualities(KNOWN_FORMATS)

        entries = []
        for audio in story.get('audio', []):
            title = audio.get('title', {}).get('$text')
            duration = int_or_none(audio.get('duration', {}).get('$text'))
            formats = []
            for format_id, formats_entry in audio.get('format', {}).items():
                if not formats_entry:
                    continue
                if isinstance(formats_entry, list):
                    formats_entry = formats_entry[0]
                format_url = formats_entry.get('$text')
                if not format_url:
                    continue
                if format_id in KNOWN_FORMATS:
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'ext': formats_entry.get('type'),
                        'quality': quality(format_id),
                    })
            self._sort_formats(formats)
            entries.append({
                'id': audio['id'],
                'title': title,
                'duration': duration,
                'formats': formats,
            })

        playlist_title = story.get('title', {}).get('$text')
        return self.playlist_result(entries, playlist_id, playlist_title)
