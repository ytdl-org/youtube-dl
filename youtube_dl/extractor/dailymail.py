# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    determine_protocol,
)


class DailyMailIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?dailymail\.co\.uk/video/[^/]+/video-(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.dailymail.co.uk/video/sciencetech/video-1288527/Turn-video-impressionist-masterpiece.html',
        'md5': '2f639d446394f53f3a33658b518b6615',
        'info_dict': {
            'id': '1288527',
            'ext': 'mp4',
            'title': 'Turn any video into an impressionist masterpiece',
            'description': 'md5:88ddbcb504367987b2708bb38677c9d2',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_data = self._parse_json(self._search_regex(
            r"data-opts='({.+?})'", webpage, 'video data'), video_id)
        title = video_data['title']
        video_sources = self._download_json(video_data.get(
            'sources', {}).get('url') or 'http://www.dailymail.co.uk/api/player/%s/video-sources.json' % video_id, video_id)

        formats = []
        for rendition in video_sources['renditions']:
            rendition_url = rendition.get('url')
            if not rendition_url:
                continue
            tbr = int_or_none(rendition.get('encodingRate'), 1000)
            container = rendition.get('videoContainer')
            is_hls = container == 'M2TS'
            protocol = 'm3u8_native' if is_hls else determine_protocol({'url': rendition_url})
            formats.append({
                'format_id': ('hls' if is_hls else protocol) + ('-%d' % tbr if tbr else ''),
                'url': rendition_url,
                'width': int_or_none(rendition.get('frameWidth')),
                'height': int_or_none(rendition.get('frameHeight')),
                'tbr': tbr,
                'vcodec': rendition.get('videoCodec'),
                'container': container,
                'protocol': protocol,
                'ext': 'mp4' if is_hls else None,
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('descr'),
            'thumbnail': video_data.get('poster') or video_data.get('thumbnail'),
            'formats': formats,
        }
