from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
    xpath_text,
    xpath_attr,
)


class NBAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:watch\.|www\.)?nba\.com/(?P<path>(?:[^/]+/)?video/(?P<id>[^?]*?))/?(?:/index\.html)?(?:\?.*)?$'
    _TESTS = [{
        'url': 'http://www.nba.com/video/games/nets/2012/12/04/0021200253-okc-bkn-recap.nba/index.html',
        'md5': '9e7729d3010a9c71506fd1248f74e4f4',
        'info_dict': {
            'id': '0021200253-okc-bkn-recap',
            'ext': 'mp4',
            'title': 'Thunder vs. Nets',
            'description': 'Kevin Durant scores 32 points and dishes out six assists as the Thunder beat the Nets in Brooklyn.',
            'duration': 181,
            'timestamp': 1354638466,
            'upload_date': '20121204',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://www.nba.com/video/games/hornets/2014/12/05/0021400276-nyk-cha-play5.nba/',
        'only_matching': True,
    }, {
        'url': 'http://watch.nba.com/video/channels/playoffs/2015/05/20/0041400301-cle-atl-recap.nba',
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

    def _real_extract(self, url):
        path, video_id = re.match(self._VALID_URL, url).groups()
        if path.startswith('nba/'):
            path = path[3:]
        video_info = self._download_xml('http://www.nba.com/%s.xml' % path, video_id)
        video_id = xpath_text(video_info, 'slug')
        title = xpath_text(video_info, 'headline')
        description = xpath_text(video_info, 'description')
        duration = parse_duration(xpath_text(video_info, 'length'))
        timestamp = int_or_none(xpath_attr(video_info, 'dateCreated', 'uts'))

        thumbnails = []
        for image in video_info.find('images'):
            thumbnails.append({
                'id': image.attrib.get('cut'),
                'url': image.text,
                'width': int_or_none(image.attrib.get('width')),
                'height': int_or_none(image.attrib.get('height')),
            })

        formats = []
        for video_file in video_info.findall('.//file'):
            video_url = video_file.text
            if video_url.startswith('/'):
                continue
            if video_url.endswith('.m3u8'):
                formats.extend(self._extract_m3u8_formats(video_url, video_id, ext='mp4', m3u8_id='hls', fatal=False))
            elif video_url.endswith('.f4m'):
                formats.extend(self._extract_f4m_formats(video_url + '?hdcore=3.4.1.1', video_id, f4m_id='hds', fatal=False))
            else:
                key = video_file.attrib.get('bitrate')
                format_info = {
                    'format_id': key,
                    'url': video_url,
                }
                mobj = re.search(r'(\d+)x(\d+)(?:_(\d+))?', key)
                if mobj:
                    format_info.update({
                        'width': int(mobj.group(1)),
                        'height': int(mobj.group(2)),
                        'tbr': int_or_none(mobj.group(3)),
                    })
                formats.append(format_info)
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
