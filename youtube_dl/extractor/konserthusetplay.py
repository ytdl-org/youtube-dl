# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
)


class KonserthusetPlayIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?konserthusetplay\.se/\?.*\bm=(?P<id>[^&]+)'
    _TEST = {
        'url': 'http://www.konserthusetplay.se/?m=CKDDnlCY-dhWAAqiMERd-A',
        'info_dict': {
            'id': 'CKDDnlCY-dhWAAqiMERd-A',
            'ext': 'flv',
            'title': 'Orkesterns instrument: Valthornen',
            'description': 'md5:f10e1f0030202020396a4d712d2fa827',
            'thumbnail': 're:^https?://.*$',
            'duration': 398.8,
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        e = self._search_regex(
            r'https?://csp\.picsearch\.com/rest\?.*\be=(.+?)[&"\']', webpage, 'e')

        rest = self._download_json(
            'http://csp.picsearch.com/rest?e=%s&containerId=mediaplayer&i=object' % e,
            video_id, transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        media = rest['media']
        player_config = media['playerconfig']
        playlist = player_config['playlist']

        source = next(f for f in playlist if f.get('bitrates'))

        FORMAT_ID_REGEX = r'_([^_]+)_h264m\.mp4'

        formats = []

        fallback_url = source.get('fallbackUrl')
        fallback_format_id = None
        if fallback_url:
            fallback_format_id = self._search_regex(
                FORMAT_ID_REGEX, fallback_url, 'format id', default=None)

        connection_url = (player_config.get('rtmp', {}).get(
            'netConnectionUrl') or player_config.get(
            'plugins', {}).get('bwcheck', {}).get('netConnectionUrl'))
        if connection_url:
            for f in source['bitrates']:
                video_url = f.get('url')
                if not video_url:
                    continue
                format_id = self._search_regex(
                    FORMAT_ID_REGEX, video_url, 'format id', default=None)
                f_common = {
                    'vbr': int_or_none(f.get('bitrate')),
                    'width': int_or_none(f.get('width')),
                    'height': int_or_none(f.get('height')),
                }
                f = f_common.copy()
                f.update({
                    'url': connection_url,
                    'play_path': video_url,
                    'format_id': 'rtmp-%s' % format_id if format_id else 'rtmp',
                    'ext': 'flv',
                })
                formats.append(f)
                if format_id and format_id == fallback_format_id:
                    f = f_common.copy()
                    f.update({
                        'url': fallback_url,
                        'format_id': 'http-%s' % format_id if format_id else 'http',
                    })
                    formats.append(f)

        if not formats and fallback_url:
            formats.append({
                'url': fallback_url,
            })

        self._sort_formats(formats)

        title = player_config.get('title') or media['title']
        description = player_config.get('mediaInfo', {}).get('description')
        thumbnail = media.get('image')
        duration = float_or_none(media.get('duration'), 1000)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
