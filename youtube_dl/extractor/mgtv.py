# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class MGTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.mgtv\.com/v/(?:[^/]+/)*(?P<id>\d+)\.html'
    IE_DESC = '芒果TV'

    _TEST = {
        'url': 'http://www.mgtv.com/v/1/290525/f/3116640.html',
        'md5': '1bdadcf760a0b90946ca68ee9a2db41a',
        'info_dict': {
            'id': '3116640',
            'ext': 'mp4',
            'title': '我是歌手第四季双年巅峰会：韩红李玟“双王”领军对抗',
            'description': '我是歌手第四季双年巅峰会',
            'duration': 7461,
            'thumbnail': 're:^https?://.*\.jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_data = self._download_json(
            'http://v.api.mgtv.com/player/video', video_id,
            query={'video_id': video_id})['data']
        info = api_data['info']

        formats = []
        for idx, stream in enumerate(api_data['stream']):
            stream_url = stream.get('url')
            if not stream_url:
                continue
            tbr = int_or_none(self._search_regex(
                r'(\d+)\.mp4', stream_url, 'tbr', default=None))

            def extract_format(stream_url, format_id, idx, query={}):
                format_info = self._download_json(
                    stream_url, video_id,
                    note='Download video info for format %s' % format_id or '#%d' % idx, query=query)
                return {
                    'format_id': format_id,
                    'url': format_info['info'],
                    'ext': 'mp4',
                    'tbr': tbr,
                }

            formats.append(extract_format(
                stream_url, 'hls-%d' % tbr if tbr else None, idx * 2))
            formats.append(extract_format(stream_url.replace(
                '/playlist.m3u8', ''), 'http-%d' % tbr if tbr else None, idx * 2 + 1, {'pno': 1031}))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'].strip(),
            'formats': formats,
            'description': info.get('desc'),
            'duration': int_or_none(info.get('duration')),
            'thumbnail': info.get('thumb'),
        }
