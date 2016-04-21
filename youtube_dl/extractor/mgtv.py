# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class MGTVIE(InfoExtractor):
    _VALID_URL = r'https?://www\.mgtv\.com/v/(?:[^/]+/)*(?P<id>\d+)\.html'
    IE_DESC = '芒果TV'

    _TEST = {
        'url': 'http://www.mgtv.com/v/1/290525/f/3116640.html',
        'md5': '',
        'info_dict': {
            'id': '3116640',
            'ext': 'mp4',
            'title': '我是歌手第四季双年巅峰会：韩红李玟“双王”领军对抗',
            'description': '我是歌手第四季双年巅峰会',
            'duration': 7461,
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'params': {
            'skip_download': True,  # m3u8 download
        },
    }

    _FORMAT_MAP = {
        '标清': ('Standard', 0),
        '高清': ('High', 1),
        '超清': ('SuperHigh', 2),
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        api_data = self._download_json(
            'http://v.api.mgtv.com/player/video', video_id,
            query={'video_id': video_id})['data']
        info = api_data['info']

        formats = []
        for idx, stream in enumerate(api_data['stream']):
            format_name = stream.get('name')
            format_id, preference = self._FORMAT_MAP.get(format_name, (None, None))
            format_info = self._download_json(
                stream['url'], video_id,
                note='Download video info for format %s' % format_id or '#%d' % idx)
            formats.append({
                'format_id': format_id,
                'url': format_info['info'],
                'ext': 'mp4',  # These are m3u8 playlists
                'preference': preference,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['title'].strip(),
            'formats': formats,
            'description': info.get('desc'),
            'duration': int_or_none(info.get('duration')),
            'thumbnail': info.get('thumb'),
        }
