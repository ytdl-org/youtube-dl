# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class SVTPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?svtplay\.se/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.svtplay.se/video/2609989/sm-veckan/sm-veckan-rally-final-sasong-1-sm-veckan-rally-final',
        'md5': 'f4a184968bc9c802a9b41316657aaa80',
        'info_dict': {
            'id': '2609989',
            'ext': 'mp4',
            'title': 'SM veckan vinter, Örebro - Rally, final',
            'duration': 4500,
            'thumbnail': 're:^https?://.*[\.-]jpg$',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            'http://www.svtplay.se/video/%s?output=json' % video_id, video_id)

        title = info['context']['title']
        thumbnail = info['context'].get('thumbnailImage')

        video_info = info['video']
        formats = []
        for vr in video_info['videoReferences']:
            vurl = vr['url']
            if determine_ext(vurl) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id,
                    ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id=vr.get('playerType')))
            else:
                formats.append({
                    'format_id': vr.get('playerType'),
                    'url': vurl,
                })
        self._sort_formats(formats)

        duration = video_info.get('materialLength')

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
        }
