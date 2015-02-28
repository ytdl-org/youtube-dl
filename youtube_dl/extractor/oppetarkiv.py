# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class OppetArkivIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?oppetarkiv\.se/video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.oppetarkiv.se/video/1058509/rederiet-sasong-1-avsnitt-1-av-318',
        'md5': '5c1eb616e59f733d4af77edc5177d2fe',
        'info_dict': {
            'id': '1058509',
            'ext': 'flv',
            'title': 'Farlig kryssning',
            'duration': 2566,
            'thumbnail': 're:^https?://.*[\.-]jpg$',
            'age_limit': 0,
        },
        'skip': 'Only works from Sweden',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            'http://www.oppetarkiv.se/video/%s?output=json' % video_id, video_id)

        title = info['context']['title']
        thumbnail = info['context'].get('thumbnailImage')

        video_info = info['video']
        formats = []
        for vr in video_info['videoReferences']:
            vurl = vr['url']
            ext = determine_ext(vurl)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id,
                    ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id=vr.get('playerType')))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    vurl + '?hdcore=3.3.0', video_id,
                    f4m_id=vr.get('playerType')))
            else:
                formats.append({
                    'format_id': vr.get('playerType'),
                    'url': vurl,
                })
        self._sort_formats(formats)

        duration = video_info.get('materialLength')

        age_limit = 18 if video_info.get('inappropriateForChildren') else 0

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': age_limit,
        }
