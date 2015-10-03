from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
)


class NBAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:watch\.|www\.)?nba\.com/(?:nba/)?video/(?P<id>[^?]*?)/?(?:/index\.html)?(?:\?.*)?$'
    _TESTS = [{
        'url': 'http://www.nba.com/video/games/nets/2012/12/04/0021200253-okc-bkn-recap.nba/index.html',
        'md5': '9d902940d2a127af3f7f9d2f3dc79c96',
        'info_dict': {
            'id': '0021200253-okc-bkn-recap',
            'ext': 'mp4',
            'title': 'Thunder vs. Nets',
            'description': 'Kevin Durant scores 32 points and dishes out six assists as the Thunder beat the Nets in Brooklyn.',
            'duration': 181,
            'timestamp': 1354638466,
            'upload_date': '20121204',
        },
    }, {
        'url': 'http://www.nba.com/video/games/hornets/2014/12/05/0021400276-nyk-cha-play5.nba/',
        'only_matching': True,
    },{
        'url': 'http://watch.nba.com/nba/video/channels/playoffs/2015/05/20/0041400301-cle-atl-recap.nba',
        'md5': 'b2b39b81cf28615ae0c3360a3f9668c4',
        'info_dict': {
            'id': '0041400301-cle-atl-recap',
            'ext': 'mp4',
            'title': 'Hawks vs. Cavaliers Game 1',
            'description': 'md5:8094c3498d35a9bd6b1a8c396a071b4d',
            'duration': 228,
            'timestamp': 1432134543,
            'upload_date': '20150520',
        }
    }]

    _BASE_PATHS = {
        'turner': 'http://nba.cdn.turner.com/nba/big',
        'akamai': 'http://nbavod-f.akamaihd.net',
    }

    _QUALITIES = {
        '420mp4': {
            'width': 400,
            'height': 224,
            'preference': 1,
        },
        '416x234': {
            'width': 416,
            'height': 234,
            'preference': 2,
        },
        '556': {
            'width': 416,
            'height': 234,
            'preference': 3,
        },
        '480x320_910': {
            'width': 480,
            'height': 320,
            'preference': 4,
        },
        'nba_576x324': {
            'width': 576,
            'height': 324,
            'preference': 5,
        },
        'nba_640x360': {
            'width': 640,
            'height': 360,
            'preference': 6,
        },
        '640x360_664b': {
            'width': 640,
            'height': 360,
            'preference': 7,
        },
        '640x360_664m': {
            'width': 640,
            'height': 360,
            'preference': 8,
        },
        '768x432_996': {
            'width': 768,
            'height': 432,
            'preference': 9,
        },
        '768x432_1404': {
            'width': 768,
            'height': 432,
            'preference': 10,
        },
        '960x540_2104': {
            'width': 960,
            'height': 540,
            'preference': 11,
        },
        '1280x720_3072': {
            'width': 1280,
            'height': 720,
            'preference': 12,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        video_info = self._download_xml('http://www.nba.com/video/%s.xml' % video_id, video_id)
        video_id = video_info.find('slug').text
        title = video_info.find('headline').text
        description = video_info.find('description').text
        duration = parse_duration(video_info.find('length').text)
        timestamp = int_or_none(video_info.find('dateCreated').attrib.get('uts'))

        thumbnails = []
        for image in video_info.find('images'):
            thumbnails.append({
                'id': image.attrib.get('cut'),
                'url': image.text,
                'width': int_or_none(image.attrib.get('width')),
                'height': int_or_none(image.attrib.get('height')),
            })

        formats = []
        for video_file in video_info.find('files').iter('file'):
            video_url = video_file.text
            if not video_url.startswith('http://'):
                if video_url.endswith('.m3u8') or video_url.endswith('.f4m'):
                    video_url = self._BASE_PATHS['akamai'] + video_url
                else:
                    video_url = self._BASE_PATHS['turner'] + video_url
            if video_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(video_url, video_id))
            elif video_url.endswith('.f4m'):
                formats.extend(self._extract_f4m_formats(video_url + '?hdcore=3.4.1.1', video_id))
            else:
                key = video_file.attrib.get('bitrate')
                quality = self._QUALITIES[key]
                formats.append({
                    'format_id': key,
                    'url': video_url,
                    'width': quality['width'],
                    'height': quality['height'],
                    'preference': quality['preference'],
                })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'timestamp': timestamp,
            'thumbnails': thumbnails,
            'formats': formats,
        }
