# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    int_or_none,
    parse_iso8601
)

class FreshliveIE(InfoExtractor):
    _VALID_URL = r'https?://freshlive\.tv/(?P<streamer>[^/]+)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://freshlive.tv/satotv/74712',
        'md5': '224f50d268b6b9f94e4198deccd55d6d',
        'info_dict': {
            'description': 'テスト',
            'duration': 1511,
            'id': '74712',
            'ext': 'mp4',
            'timestamp': 1483621764,
            'title': 'テスト',
            'thumbnail': r're:^https?://.*\.jpg$',
            'upload_date': '20170105',
            'uploader': 'サトTV',
            'uploader_id': 'satotv',
            'view_count': int,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        options = self._parse_json(
            self._search_regex(
                r'window\.__CONTEXT__\s*=\s*({.+?});\s*</script>',
                webpage, 'initial context'),
            video_id)

        programs = options['context']['dispatcher']['stores']['ProgramStore']['programs']
        info = programs.get(video_id, {})

        video_url = info.get('liveStreamUrl') or info.get('archiveStreamUrl')
        if not video_url:
            raise ExtractorError('%s not a valid broadcast ID' % video_id, expected=True)

        formats = self._extract_m3u8_formats(
            video_url, video_id, ext='mp4', m3u8_id='hls')

        return {
            'id': video_id,
            'formats': formats,
            'title': info.get('title'),
            'description': info.get('description'),
            'duration': int_or_none(info.get('airTime')),
            'is_live': int_or_none(info.get('airTime')) == None,
            'thumbnail': info.get('thumbnailUrl'),
            'uploader': info.get('channel', {}).get('title'),
            'uploader_id': info.get('channel', {}).get('code'),
            'uploader_url': info.get('channel', {}).get('permalink'),
            'timestamp': parse_iso8601(info.get('startAt')),
            'view_count': int_or_none(info.get('viewCount')),
        }