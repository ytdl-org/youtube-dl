# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    try_get,
    float_or_none,
    int_or_none
)


class MedalTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?medal\.tv/clips/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://medal.tv/clips/34934644/3Is9zyGMoBMr',
        'md5': '7b07b064331b1cf9e8e5c52a06ae68fa',
        'info_dict': {
            'id': '34934644',
            'ext': 'mp4',
            'title': 'Quad Cold',
            'description': 'Medal,https://medal.tv/desktop/',
            'uploader': 'MowgliSB',
            'timestamp': 1603165266,
            'upload_date': '20201020',
            'uploader_id': 10619174,
        }
    }, {
        'url': 'https://medal.tv/clips/36787208',
        'md5': 'b6dc76b78195fff0b4f8bf4a33ec2148',
        'info_dict': {
            'id': '36787208',
            'ext': 'mp4',
            'title': 'u tk me i tk u bigger',
            'description': 'Medal,https://medal.tv/desktop/',
            'uploader': 'Mimicc',
            'timestamp': 1605580939,
            'upload_date': '20201117',
            'uploader_id': 5156321,
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        hydration_data = self._search_regex(
            r'<script[^>]*>\s*(?:var\s*)?hydrationData\s*=\s*({.+?})\s*</script>',
            webpage, 'hydration data', default='{}')
        parsed = self._parse_json(hydration_data, video_id)

        clip_info = try_get(parsed, lambda x: x['clips'][video_id], dict) or {}
        if not clip_info:
            raise ExtractorError('Could not find video information.',
                                 video_id=video_id)

        width = int_or_none(clip_info.get('sourceWidth'))
        height = int_or_none(clip_info.get('sourceHeight'))

        aspect_ratio = (width / height) if(width and height) else (16 / 9)

        # ordered from lowest to highest resolution
        heights = (144, 240, 360, 480, 720, 1080)

        formats = []
        thumbnails = []

        for height in heights:
            format_key = '{0}p'.format(height)
            video_key = 'contentUrl{0}'.format(format_key)
            thumbnail_key = 'thumbnail{0}'.format(format_key)
            width = int(round(aspect_ratio * height))

            # Second condition needed as sometimes medal says
            # they have a format when in fact it is another format.
            format_url = clip_info.get(video_key)
            if(format_url and format_key in format_url):
                formats.append({
                    'url': format_url,
                    'format_id': format_key,
                    'width': width,
                    'height': height
                })

            thumbnail_url = clip_info.get(thumbnail_key)
            if(thumbnail_url and format_key in thumbnail_url):
                thumbnails.append({
                    'id': format_key,
                    'url': thumbnail_url,
                    'width': width,
                    'height': height
                })

        # add source to formats
        source_url = clip_info.get('contentUrl')
        if(source_url):
            formats.append({
                'url': source_url,
                'format_id': 'source',
                'width': width,
                'height': height
            })

        error = clip_info.get('error')
        if not formats and error:
            if(error == 404):
                raise ExtractorError('That clip does not exist.',
                                     expected=True, video_id=video_id)
            else:
                raise ExtractorError('An unknown error occurred ({0}).'.format(error),
                                     video_id=video_id)

        # Necessary because the id of the author is not known in advance.
        # Won't raise an issue if no profile can be found as this is optional.
        author_info = try_get(parsed,
                              lambda x: list(x['profiles'].values())[0], dict
                              ) or {}
        author_id = author_info.get('id')
        author_url = 'https://medal.tv/users/{0}'.format(author_id) if author_id else None

        return {
            'id': video_id,
            'title': clip_info.get('contentTitle'),
            'formats': formats,
            'thumbnails': thumbnails,
            'description': clip_info.get('contentDescription'),

            'uploader': author_info.get('displayName'),
            'timestamp': float_or_none(clip_info.get('created'), 1000),
            'uploader_id': author_id,
            'uploader_url': author_url,

            'duration': float_or_none(clip_info.get('videoLengthSeconds')),
            'view_count': int_or_none(clip_info.get('views')),
            'like_count': int_or_none(clip_info.get('likes')),
            'comment_count': int_or_none(clip_info.get('comments'))
        }
