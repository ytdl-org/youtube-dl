# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
)


class SVTPlayIE(InfoExtractor):
    IE_DESC = 'SVT Play and Öppet arkiv'
    _VALID_URL = r'https?://(?:www\.)?(?P<host>svtplay|oppetarkiv)\.se/video/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.svtplay.se/video/2609989/sm-veckan/sm-veckan-rally-final-sasong-1-sm-veckan-rally-final',
        'md5': 'ade3def0643fa1c40587a422f98edfd9',
        'info_dict': {
            'id': '2609989',
            'ext': 'flv',
            'title': 'SM veckan vinter, Örebro - Rally, final',
            'duration': 4500,
            'thumbnail': 're:^https?://.*[\.-]jpg$',
            'age_limit': 0,
        },
    }, {
        'url': 'http://www.oppetarkiv.se/video/1058509/rederiet-sasong-1-avsnitt-1-av-318',
        'md5': 'c3101a17ce9634f4c1f9800f0746c187',
        'info_dict': {
            'id': '1058509',
            'ext': 'flv',
            'title': 'Farlig kryssning',
            'duration': 2566,
            'thumbnail': 're:^https?://.*[\.-]jpg$',
            'age_limit': 0,
        },
        'skip': 'Only works from Sweden',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        host = mobj.group('host')

        info = self._download_json(
            'http://www.%s.se/video/%s?output=json' % (host, video_id), video_id)

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
