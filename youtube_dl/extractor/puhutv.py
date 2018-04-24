# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_str
)


class PuhuTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?puhutv\.com/(?P<id>[a-z0-9-]+)-izle'
    _TESTS = [
        {
            'url': 'https://puhutv.com/sut-kardesler-izle',
            'md5': '51f11ccdeef908753b4e3a99d19be939',
            'info_dict': {
                'id': '5085',
                'slug_id': 'sut-kardesler',
                'ext': 'mp4',
                'title': 'Süt Kardeşler',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'Arzu Film',
                'description': 'md5:405fd024df916ca16731114eb18e511a',
            },
        },
        {
            'url': 'https://puhutv.com/jet-sosyete-1-bolum-izle',
            'only_matching': True,
        }
    ]
    IE_NAME = 'puhutv'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = self._download_json(
            'https://puhutv.com/api/slug/%s-izle' % video_id,
            video_id).get('data')

        id = compat_str(info.get('id'))
        title = info.get('title').get('name')
        if(info.get('display_name')):
            title += ' ' + info.get('display_name')

        thumbnails = []
        for key,image in info.get('content').get('images').get('wide').items():
            thumbnails.append({
                'url': image,
                'id': key
            })

        format_dict = self._download_json(
            'https://puhutv.com/api/assets/%s/videos' % id,
            id, 'Downloading sources').get('data').get('videos')
        if not format_dict:
            raise ExtractorError('This video not available in your country')

        formats = []
        for format in format_dict:
            media_url = format.get('url')
            ext = format.get('video_format')
            quality = format.get('quality')
            if ext == 'hls':
                format_id = 'hls-%s' % quality
                formats.extend(self._extract_m3u8_formats(
                    media_url, id, 'm3u8', preference=-1,
                    m3u8_id=format_id, fatal=False))
            else:
                if format.get('is_playlist') == False:
                    formats.append({
                        'url': media_url,
                        'format_id': 'http-%s' % quality,
                        'ext': ext
                    })
        self._sort_formats(formats)

        return {
            'id': id,
            'slug_id': video_id,
            'title': title,
            'description': info.get('title').get('description'),
            'uploader': info.get('title').get('producer').get('name'),
            'view_count': info.get('content').get('watch_count'),
            'follower_count': info.get('title').get('follower_count'),
            'thumbnail': 'https://%s' % info.get('content').get('images').get('wide').get('main'),
            'thumbnails': thumbnails,
            'loop_thumbnails': info.get('content').get('loop_thumbnails'),
            'formats': formats
        }
