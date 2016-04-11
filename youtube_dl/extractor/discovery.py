from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)
from ..compat import compat_str


class DiscoveryIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://(?:www\.)?(?:
            discovery|
            investigationdiscovery|
            discoverylife|
            animalplanet|
            ahctv|
            destinationamerica|
            sciencechannel|
            tlc|
            velocity
        )\.com/(?:[^/]+/)*(?P<id>[^./?#]+)'''
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
            'timestamp': 1302032462,
            'upload_date': '20110405',
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
        'playlist_mincount': 10,
    }, {
        'url': 'http://www.animalplanet.com/longfin-eels-maneaters/',
        'info_dict': {
            'id': '78326',
            'ext': 'mp4',
            'title': 'Longfin Eels: Maneaters?',
            'description': 'Jeremy Wade tests whether or not New Zealand\'s longfin eels are man-eaters by covering himself in fish guts and getting in the water with them.',
            'upload_date': '20140725',
            'timestamp': 1406246400,
            'duration': 116,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        info = self._download_json(url + '?flat=1', display_id)

        video_title = info.get('playlist_title') or info.get('video_title')

        entries = []

        for idx, video_info in enumerate(info['playlist']):
            formats = self._extract_m3u8_formats(
                video_info['src'], display_id, 'mp4', 'm3u8_native', m3u8_id='hls',
                note='Download m3u8 information for video %d' % (idx + 1))
            self._sort_formats(formats)
            entries.append({
                'id': compat_str(video_info['id']),
                'formats': formats,
                'title': video_info['title'],
                'description': video_info.get('description'),
                'duration': parse_duration(video_info.get('video_length')),
                'webpage_url': video_info.get('href') or video_info.get('url'),
                'thumbnail': video_info.get('thumbnailURL'),
                'alt_title': video_info.get('secondary_title'),
                'timestamp': parse_iso8601(video_info.get('publishedDate')),
            })

        return self.playlist_result(entries, display_id, video_title)
