# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    float_or_none
)


class StreamableIE(InfoExtractor):
    _VALID_URL = r'https?://streamable\.com/(?P<id>[\w]+)'
    _TESTS = [
        {
            'url': 'https://streamable.com/dnd1',
            'md5': '3e3bc5ca088b48c2d436529b64397fef',
            'info_dict': {
                'id': 'dnd1',
                'ext': 'mp4',
                'title': 'Mikel Oiarzabal scores to make it 0-3 for La Real against Espanyol',
                'thumbnail': 'http://cdn.streamable.com/image/dnd1.jpg',
            }
        },
        # older video without bitrate, width/height, etc. info
        {
            'url': 'https://streamable.com/moo',
            'md5': '2cf6923639b87fba3279ad0df3a64e73',
            'info_dict': {
                'id': 'moo',
                'ext': 'mp4',
                'title': '"Please don\'t eat me!"',
                'thumbnail': 'http://cdn.streamable.com/image/f6441ae0c84311e4af010bc47400a0a4.jpg',
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # Note: Using the ajax API, as the public Streamable API doesn't seem
        # to return video info like the title properly sometimes, and doesn't
        # include info like the video duration
        video = self._download_json(
            'https://streamable.com/ajax/videos/%s' % video_id, video_id)

        # Format IDs:
        # 0 The video is being uploaded
        # 1 The video is being processed
        # 2 The video has at least one file ready
        # 3 The video is unavailable due to an error
        status = video.get('status')
        if status != 2:
            raise ExtractorError(
                'This video is currently unavailable. It may still be uploading or processing.',
                expected=True)

        formats = []
        for key, info in video.get('files').items():
            formats.append({
                'format_id': key,
                'url': info['url'],
                'width': info.get('width'),
                'height': info.get('height'),
                'filesize': info.get('size'),
                'fps': info.get('framerate'),
                'vbr': float_or_none(info.get('bitrate'), 1000)
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video.get('result_title'),
            'thumbnail': video.get('thumbnail_url'),
            'duration': video.get('duration'),
            'formats': formats
        }
