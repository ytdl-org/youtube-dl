# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    float_or_none,
    parse_duration,
    str_to_int,
    urlencode_postdata,
)


class PandoraTVIE(InfoExtractor):
    IE_NAME = 'pandora.tv'
    IE_DESC = '판도라TV'
    _VALID_URL = r'https?://(?:.+?\.)?channel\.pandora\.tv/channel/video\.ptv\?'
    _TEST = {
        'url': 'http://jp.channel.pandora.tv/channel/video.ptv?c1=&prgid=53294230&ch_userid=mikakim&ref=main&lot=cate_01_2',
        'info_dict': {
            'id': '53294230',
            'ext': 'flv',
            'title': '頭を撫でてくれる？',
            'description': '頭を撫でてくれる？',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 39,
            'upload_date': '20151218',
            'uploader': 'カワイイ動物まとめ',
            'uploader_id': 'mikakim',
            'view_count': int,
            'like_count': int,
        }
    }

    def _real_extract(self, url):
        qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        video_id = qs.get('prgid', [None])[0]
        user_id = qs.get('ch_userid', [None])[0]
        if any(not f for f in (video_id, user_id,)):
            raise ExtractorError('Invalid URL', expected=True)

        data = self._download_json(
            'http://m.pandora.tv/?c=view&m=viewJsonApi&ch_userid=%s&prgid=%s'
            % (user_id, video_id), video_id)

        info = data['data']['rows']['vod_play_info']['result']

        formats = []
        for format_id, format_url in info.items():
            if not format_url:
                continue
            height = self._search_regex(
                r'^v(\d+)[Uu]rl$', format_id, 'height', default=None)
            if not height:
                continue

            play_url = self._download_json(
                'http://m.pandora.tv/?c=api&m=play_url', video_id,
                data=urlencode_postdata({
                    'prgid': video_id,
                    'runtime': info.get('runtime'),
                    'vod_url': format_url,
                }),
                headers={
                    'Origin': url,
                    'Content-Type': 'application/x-www-form-urlencoded',
                })
            format_url = play_url.get('url')
            if not format_url:
                continue

            formats.append({
                'format_id': '%sp' % height,
                'url': format_url,
                'height': int(height),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': info['subject'],
            'description': info.get('body'),
            'thumbnail': info.get('thumbnail') or info.get('poster'),
            'duration': float_or_none(info.get('runtime'), 1000) or parse_duration(info.get('time')),
            'upload_date': info['fid'][:8] if isinstance(info.get('fid'), compat_str) else None,
            'uploader': info.get('nickname'),
            'uploader_id': info.get('upload_userid'),
            'view_count': str_to_int(info.get('hit')),
            'like_count': str_to_int(info.get('likecnt')),
            'formats': formats,
        }
