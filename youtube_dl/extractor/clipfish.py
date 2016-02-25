from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)


class ClipfishIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?clipfish\.de/(?:[^/]+/)+video/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.clipfish.de/special/game-trailer/video/3966754/fifa-14-e3-2013-trailer/',
        'md5': '79bc922f3e8a9097b3d68a93780fd475',
        'info_dict': {
            'id': '3966754',
            'ext': 'mp4',
            'title': 'FIFA 14 - E3 2013 Trailer',
            'description': 'Video zu FIFA 14: E3 2013 Trailer',
            'upload_date': '20130611',
            'duration': 82,
            'view_count': int,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video_info = self._download_json(
            'http://www.clipfish.de/devapi/id/%s?format=json&apikey=hbbtv' % video_id,
            video_id)['items'][0]

        formats = []

        m3u8_url = video_info.get('media_videourl_hls')
        if m3u8_url:
            formats.append({
                'url': m3u8_url.replace('de.hls.fra.clipfish.de', 'hls.fra.clipfish.de'),
                'ext': 'mp4',
                'format_id': 'hls',
            })

        mp4_url = video_info.get('media_videourl')
        if mp4_url:
            formats.append({
                'url': mp4_url,
                'format_id': 'mp4',
                'width': int_or_none(video_info.get('width')),
                'height': int_or_none(video_info.get('height')),
                'tbr': int_or_none(video_info.get('bitrate')),
            })

        return {
            'id': video_id,
            'title': video_info['title'],
            'description': video_info.get('descr'),
            'formats': formats,
            'thumbnail': video_info.get('media_content_thumbnail_large') or video_info.get('media_thumbnail'),
            'duration': int_or_none(video_info.get('media_length')),
            'upload_date': unified_strdate(video_info.get('pubDate')),
            'view_count': int_or_none(video_info.get('media_views'))
        }
