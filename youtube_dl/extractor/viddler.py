from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
)
from ..compat import (
   compat_urllib_request
)


class ViddlerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?viddler\.com/(?:v|embed|player)/(?P<id>[a-z0-9]+)'
    _TESTS = [{
        "url": "http://www.viddler.com/v/43903784",
        'md5': 'ae43ad7cb59431ce043f0ff7fa13cbf4',
        'info_dict': {
            'id': '43903784',
            'ext': 'mp4',
            "title": "Video Made Easy",
            'description': 'You don\'t need to be a professional to make high-quality video content. Viddler provides some quick and easy tips on how to produce great video content with limited resources. ',
            "uploader": "viddler",
            'timestamp': 1335371429,
            'upload_date': '20120425',
            "duration": 100.89,
            'thumbnail': 're:^https?://.*\.jpg$',
            'view_count': int,
            'categories': ['video content', 'high quality video', 'video made easy', 'how to produce video with limited resources', 'viddler'],
        }
    }, {
        "url": "http://www.viddler.com/v/4d03aad9/",
        "file": "4d03aad9.mp4",
        "md5": "faa71fbf70c0bee7ab93076fd007f4b0",
        "info_dict": {
            'upload_date': '20150126',
            'uploader': 'deadspin',
            'id': '4d03aad9',
            'timestamp': 1422285291,
            'title': 'WALL-TO-GORTAT',
        }
    }, {
        "url": "http://www.viddler.com/player/221ebbbd/0/",
        "file": "221ebbbd.mp4",
        "md5": "0defa2bd0ea613d14a6e9bd1db6be326",
        "info_dict": {
            'upload_date': '20140929',
            'uploader': 'BCLETeens',
            'id': '221ebbbd',
            'timestamp': 1411997190,
            'title': 'LETeens-Grammar-snack-third-conditional',
            'description': ' '
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_url = (
            'http://api.viddler.com/api/v2/viddler.videos.getPlaybackDetails.json?video_id=%s&key=v0vhrt7bg2xq1vyxhkct' %
            video_id)
        headers = {'Referer': 'http://static.cdn-ec.viddler.com/js/arpeggio/v2/embed.html'}
        request = compat_urllib_request.Request(json_url, None, headers)
        data = self._download_json(request, video_id)['video']

        formats = []
        for filed in data['files']:
            if filed.get('status', 'ready') != 'ready':
                continue
            f = {
                'format_id': filed['profile_id'],
                'format_note': filed['profile_name'],
                'url': self._proto_relative_url(filed['url']),
                'width': int_or_none(filed.get('width')),
                'height': int_or_none(filed.get('height')),
                'filesize': int_or_none(filed.get('size')),
                'ext': filed.get('ext'),
                'source_preference': -1,
            }
            formats.append(f)

            if filed.get('cdn_url'):
                f = f.copy()
                f['url'] = self._proto_relative_url(filed['cdn_url'], 'http:')
                f['format_id'] = filed['profile_id'] + '-cdn'
                f['source_preference'] = 1
                formats.append(f)

            if filed.get('html5_video_source'):
                f = f.copy()
                f['url'] = self._proto_relative_url(
                    filed['html5_video_source'])
                f['format_id'] = filed['profile_id'] + '-html5'
                f['source_preference'] = 0
                formats.append(f)
        self._sort_formats(formats)

        categories = [
            t.get('text') for t in data.get('tags', []) if 'text' in t]

        return {
            '_type': 'video',
            'id': video_id,
            'title': data['title'],
            'formats': formats,
            'description': data.get('description'),
            'timestamp': int_or_none(data.get('upload_time')),
            'thumbnail': self._proto_relative_url(data.get('thumbnail_url')),
            'uploader': data.get('author'),
            'duration': float_or_none(data.get('length')),
            'view_count': int_or_none(data.get('view_count')),
            'categories': categories,
        }
