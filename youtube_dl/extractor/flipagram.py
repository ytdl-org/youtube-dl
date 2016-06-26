# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    int_or_none,
    parse_iso8601,
    unified_strdate,
    unified_timestamp,
)


class FlipagramIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?flipagram\.com/f/(?P<id>[^/?_]+)'
    _TESTS = [{
        'url': 'https://flipagram.com/f/myrWjW9RJw',
        'md5': '541988fb6c4c7c375215ea22a4a21841',
        'info_dict': {
            'id': 'myrWjW9RJw',
            'title': 'Flipagram by crystaldolce featuring King and Lionheart by Of Monsters and Men',
            'description': 'Herbie\'s first bannana🍌🐢🍌.  #animals #pets #reptile #tortoise #sulcata #tort #justatreat #snacktime #bannanas #rescuepets  #ofmonstersandmen  @animals',
            'ext': 'mp4',
            'uploader': 'Crystal Dolce',
            'creator': 'Crystal Dolce',
            'uploader_id': 'crystaldolce',
        }
    }, {
        'url': 'https://flipagram.com/f/nyvTSJMKId',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)
        user_data = self._parse_json(self._search_regex(r'window.reactH2O\s*=\s*({.+});', webpage, 'user data'), video_id)
        content_data = self._search_json_ld(webpage, video_id)

        flipagram = user_data.get('flipagram', {})
        counts = flipagram.get('counts', {})
        user = flipagram.get('user', {})
        video = flipagram.get('video', {})

        thumbnails = []
        for cover in flipagram.get('covers', []):
            if not cover.get('url'):
                continue
            thumbnails.append({
                'url': self._proto_relative_url(cover.get('url')),
                'width': int_or_none(cover.get('width')),
                'height': int_or_none(cover.get('height')),
            })

        # Note that this only retrieves comments that are initally loaded.
        # For videos with large amounts of comments, most won't be retrieved.
        comments = []
        for comment in user_data.get('comments', {}).get(video_id, {}).get('items', []):
            text = comment.get('comment', [])
            comments.append({
                'author': comment.get('user', {}).get('name'),
                'author_id': comment.get('user', {}).get('username'),
                'id': comment.get('id'),
                'text': text[0] if text else '',
                'timestamp': unified_timestamp(comment.get('created', '')),
            })

        tags = [tag for item in flipagram['story'][1:] for tag in item]

        formats = []
        if flipagram.get('music', {}).get('track', {}).get('previewUrl', {}):
            formats.append({
                'url': flipagram.get('music').get('track').get('previewUrl'),
                'ext': 'm4a',
                'vcodec': 'none',
            })

        formats.append({
            'url': video.get('url'),
            'ext': 'mp4',
            'width': int_or_none(video.get('width')),
            'height': int_or_none(video.get('height')),
            'filesize': int_or_none(video.get('size')),
        })

        return {
            'id': video_id,
            'title': content_data['title'],
            'formats': formats,
            'thumbnails': thumbnails,
            'description': content_data.get('description'),
            'uploader': user.get('name'),
            'creator': user.get('name'),
            'timestamp': parse_iso8601(flipagram.get('iso801Created')),
            'upload_date': unified_strdate(flipagram.get('created')),
            'uploader_id': user.get('username'),
            'view_count': int_or_none(counts.get('plays')),
            'repost_count': int_or_none(counts.get('reflips')),
            'comment_count': int_or_none(counts.get('comments')),
            'comments': comments,
            'tags': tags,
        }
