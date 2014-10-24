from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
)


class ViddlerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?viddler\.com/(?:v|embed|player)/(?P<id>[a-z0-9]+)'
    _TEST = {
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
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        json_url = (
            'http://api.viddler.com/api/v2/viddler.videos.getPlaybackDetails.json?video_id=%s&key=v0vhrt7bg2xq1vyxhkct' %
            video_id)
        data = self._download_json(json_url, video_id)['video']

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
                f['url'] = self._proto_relative_url(filed['cdn_url'])
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
