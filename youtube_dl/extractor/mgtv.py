# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none


class MGTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mgtv\.com/(v|b)/(?:[^/]+/)*(?P<id>\d+)\.html'
    IE_DESC = '芒果TV'

    _TESTS = [{
        'url': 'http://www.mgtv.com/v/1/290525/f/3116640.html',
        'md5': 'b1ffc0fc163152acf6beaa81832c9ee7',
        'info_dict': {
            'id': '3116640',
            'ext': 'mp4',
            'title': '我是歌手第四季双年巅峰会：韩红李玟“双王”领军对抗',
            'description': '我是歌手第四季双年巅峰会',
            'duration': 7461,
            'thumbnail': r're:^https?://.*\.jpg$',
        },
    }, {
        'url': 'http://www.mgtv.com/b/301817/3826653.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_data = self._download_json(
            'http://pcweb.api.mgtv.com/player/video', video_id,
            query={'video_id': video_id},
            headers=self.geo_verification_headers())['data']
        info = api_data['info']
        title = info['title'].strip()
        stream_domain = api_data['stream_domain'][0]

        formats = []
        for idx, stream in enumerate(api_data['stream']):
            stream_path = stream.get('url')
            if not stream_path:
                continue
            format_data = self._download_json(
                stream_domain + stream_path, video_id,
                note='Download video info for format #%d' % idx)
            format_url = format_data.get('info')
            if not format_url:
                continue
            tbr = int_or_none(self._search_regex(
                r'_(\d+)_mp4/', format_url, 'tbr', default=None))
            formats.append({
                'format_id': compat_str(tbr or idx),
                'url': format_url,
                'ext': 'mp4',
                'tbr': tbr,
                'protocol': 'm3u8_native',
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': info.get('desc'),
            'duration': int_or_none(info.get('duration')),
            'thumbnail': info.get('thumb'),
        }
