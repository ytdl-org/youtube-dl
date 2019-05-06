# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import compat_str


class IaiIE(InfoExtractor):
    IE_NAME = 'IAI'
    _VALID_URL = r'https://iai.tv/video/(?P<id>[^/#?]+)'
    _TESTS = [{
        'url': 'https://iai.tv/video/darkness-authority-and-dreams',
        'md5': '633f3175a9be21a10bc0583acc5d06bb',
        'info_dict': {
            'id': '1027',
            'ext': 'mp4',
            'title': 'How Much Authority Should Governments Have? ',
            'description': 'md5:1dbbaabf0609bcb45220b2b7d9ad063f',
            'upload_date': '20190404',
            'timestamp': 1554379576,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        data = self._search_regex(r'\bwindow\.JS_VARS\s*=\s*(\{.*\})', webpage, 'JS_VARS')
        data = self._parse_json(data, video_id)
        formats = []
        for widget in data['Widgets']['widgets']:
            if widget.get('Type') != 'VideoPlayerWidget':
                continue
            sprops = widget['Sprops']
            video_id = compat_str(sprops.get('VideoID', video_id))
            for format_id in 'sd', 'hd':
                quality = 1 if format_id == 'hd' else 0
                key = ('HighRes' if quality > 0 else '') + 'StreamingUrl'
                video_url = sprops.get(key)
                if not video_url:
                    continue
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'quality': quality,
                })
            break
        self._sort_formats(formats)
        info = self._search_json_ld(webpage, video_id, default={})
        info['id'] = video_id
        info['formats'] = formats
        if 'title' not in info:
            # title should normally be in json-ld,
            # but sometimes it's malformed
            info['title'] = self._og_search_title(webpage)
        return info
