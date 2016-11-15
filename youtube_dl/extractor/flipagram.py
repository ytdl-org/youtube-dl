# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    float_or_none,
    try_get,
    unified_timestamp,
)


class FlipagramIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?flipagram\.com/f/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://flipagram.com/f/nyvTSJMKId',
        'md5': '888dcf08b7ea671381f00fab74692755',
        'info_dict': {
            'id': 'nyvTSJMKId',
            'ext': 'mp4',
            'title': 'Flipagram by sjuria101 featuring Midnight Memories by One Direction',
            'description': 'md5:d55e32edc55261cae96a41fa85ff630e',
            'duration': 35.571,
            'timestamp': 1461244995,
            'upload_date': '20160421',
            'uploader': 'kitty juria',
            'uploader_id': 'sjuria101',
            'creator': 'kitty juria',
            'view_count': int,
            'like_count': int,
            'repost_count': int,
            'comment_count': int,
            'comments': list,
            'formats': 'mincount:2',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_data = self._parse_json(
            self._search_regex(
                r'window\.reactH2O\s*=\s*({.+});', webpage, 'video data'),
            video_id)

        flipagram = video_data['flipagram']
        video = flipagram['video']

        json_ld = self._search_json_ld(webpage, video_id, default={})
        title = json_ld.get('title') or flipagram['captionText']
        description = json_ld.get('description') or flipagram.get('captionText')

        formats = [{
            'url': video['url'],
            'width': int_or_none(video.get('width')),
            'height': int_or_none(video.get('height')),
            'filesize': int_or_none(video_data.get('size')),
        }]

        preview_url = try_get(
            flipagram, lambda x: x['music']['track']['previewUrl'], compat_str)
        if preview_url:
            formats.append({
                'url': preview_url,
                'ext': 'm4a',
                'vcodec': 'none',
            })

        self._sort_formats(formats)

        counts = flipagram.get('counts', {})
        user = flipagram.get('user', {})
        video_data = flipagram.get('video', {})

        thumbnails = [{
            'url': self._proto_relative_url(cover['url']),
            'width': int_or_none(cover.get('width')),
            'height': int_or_none(cover.get('height')),
            'filesize': int_or_none(cover.get('size')),
        } for cover in flipagram.get('covers', []) if cover.get('url')]

        # Note that this only retrieves comments that are initally loaded.
        # For videos with large amounts of comments, most won't be retrieved.
        comments = []
        for comment in video_data.get('comments', {}).get(video_id, {}).get('items', []):
            text = comment.get('comment')
            if not text or not isinstance(text, list):
                continue
            comments.append({
                'author': comment.get('user', {}).get('name'),
                'author_id': comment.get('user', {}).get('username'),
                'id': comment.get('id'),
                'text': text[0],
                'timestamp': unified_timestamp(comment.get('created')),
            })

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': float_or_none(flipagram.get('duration'), 1000),
            'thumbnails': thumbnails,
            'timestamp': unified_timestamp(flipagram.get('iso8601Created')),
            'uploader': user.get('name'),
            'uploader_id': user.get('username'),
            'creator': user.get('name'),
            'view_count': int_or_none(counts.get('plays')),
            'like_count': int_or_none(counts.get('likes')),
            'repost_count': int_or_none(counts.get('reflips')),
            'comment_count': int_or_none(counts.get('comments')),
            'comments': comments,
            'formats': formats,
        }
