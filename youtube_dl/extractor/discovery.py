from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)
from ..compat import compat_str


class DiscoveryIE(InfoExtractor):
    _VALID_URL = r'http://www\.discovery\.com\/[a-zA-Z0-9\-]*/[a-zA-Z0-9\-]*/videos/(?P<id>[a-zA-Z0-9_\-]*)(?:\.htm)?'
    _TESTS = [{
        'url': 'http://www.discovery.com/tv-shows/mythbusters/videos/mission-impossible-outtakes.htm',
        'info_dict': {
            'id': '20769',
            'ext': 'mp4',
            'title': 'Mission Impossible Outtakes',
            'description': ('Watch Jamie Hyneman and Adam Savage practice being'
                            ' each other -- to the point of confusing Jamie\'s dog -- and '
                            'don\'t miss Adam moon-walking as Jamie ... behind Jamie\'s'
                            ' back.'),
            'duration': 156,
            'timestamp': 1303099200,
            'upload_date': '20110418',
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
        }
    }, {
        'url': 'http://www.discovery.com/tv-shows/mythbusters/videos/mythbusters-the-simpsons',
        'info_dict': {
            'id': 'mythbusters-the-simpsons',
            'title': 'MythBusters: The Simpsons',
        },
        'playlist_count': 9,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(url + '?flat=1', video_id)

        video_title = info.get('playlist_title') or info.get('video_title')

        entries = [{
            'id': compat_str(video_info['id']),
            'formats': self._extract_m3u8_formats(
                video_info['src'], video_id, ext='mp4',
                note='Download m3u8 information for video %d' % (idx + 1)),
            'title': video_info['title'],
            'description': video_info.get('description'),
            'duration': parse_duration(video_info.get('video_length')),
            'webpage_url': video_info.get('href'),
            'thumbnail': video_info.get('thumbnailURL'),
            'alt_title': video_info.get('secondary_title'),
            'timestamp': parse_iso8601(video_info.get('publishedDate')),
        } for idx, video_info in enumerate(info['playlist'])]

        return self.playlist_result(entries, video_id, video_title)
