from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    parse_iso8601,
)
from ..compat import (
    compat_str,
    compat_urlparse,
)


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
            m3u8_url = video_info['src']
            formats = m3u8_formats = self._extract_m3u8_formats(
                m3u8_url, display_id, 'mp4', 'm3u8_native', m3u8_id='hls',
                note='Download m3u8 information for video %d' % (idx + 1))
            qualities_basename = self._search_regex(
                '/([^/]+)\.csmil/', m3u8_url, 'qualities basename', default=None)
            if qualities_basename:
                m3u8_path = compat_urlparse.urlparse(m3u8_url).path
                QUALITIES_RE = r'((,\d+k)+,?)'
                qualities = self._search_regex(
                    QUALITIES_RE, qualities_basename,
                    'qualities', default=None)
                if qualities:
                    qualities = list(map(lambda q: int(q[:-1]), qualities.strip(',').split(',')))
                    qualities.sort()
                    http_path = m3u8_path[1:].split('/', 1)[1]
                    http_template = re.sub(QUALITIES_RE, r'%dk', http_path)
                    http_template = http_template.replace('.csmil/master.m3u8', '')
                    http_template = compat_urlparse.urljoin(
                        'http://discsmil.edgesuite.net/', http_template)
                    if m3u8_formats:
                        self._sort_formats(m3u8_formats)
                        m3u8_formats = list(filter(
                            lambda f: f.get('vcodec') != 'none' and f.get('resolution') != 'multiple',
                            m3u8_formats))
                    if len(qualities) == len(m3u8_formats):
                        for q, m3u8_format in zip(qualities, m3u8_formats):
                            f = m3u8_format.copy()
                            f.update({
                                'url': http_template % q,
                                'format_id': f['format_id'].replace('hls', 'http'),
                                'protocol': 'http',
                            })
                            formats.append(f)
                    else:
                        for q in qualities:
                            formats.append({
                                'url': http_template % q,
                                'ext': 'mp4',
                                'format_id': 'http-%d' % q,
                                'tbr': q,
                            })
            self._sort_formats(formats)

            subtitles = []
            caption_url = video_info.get('captionsUrl')
            if caption_url:
                subtitles = {
                    'en': [{
                        'url': caption_url,
                    }]
                }

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
                'subtitles': subtitles,
            })

        return self.playlist_result(entries, display_id, video_title)
