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
            'uploader_id': '103207',
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
            'uploader_id': '103207',
        },
        'params': {
            'skip_download': True,  # requires ffmpeg
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        info = self._download_json(url + '?flat=1', display_id)

        video_title = info.get('playlist_title') or info.get('video_title')

        entries = []

        for idx, video_info in enumerate(info['playlist']):
            subtitles = {}
            caption_url = video_info.get('captionsUrl')
            if caption_url:
                subtitles = {
                    'en': [{
                        'url': caption_url,
                    }]
                }

            entries.append({
                '_type': 'url_transparent',
                'url': 'http://players.brightcove.net/103207/default_default/index.html?videoId=ref:%s' % video_info['referenceId'],
                'id': compat_str(video_info['id']),
                'title': video_info['title'],
                'description': video_info.get('description'),
                'duration': parse_duration(video_info.get('video_length')),
                'webpage_url': video_info.get('href') or video_info.get('url'),
                'thumbnail': video_info.get('thumbnailURL'),
                'alt_title': video_info.get('secondary_title'),
                'timestamp': parse_iso8601(video_info.get('publishedDate')),
                'subtitles': subtitles,
            })

        return self.playlist_result(entries, display_id, video_title)
