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

        hydration_data = self._search_regex(r'<script>.*hydrationData\s*=\s*({.+?})\s*</script>', webpage, 'hydration data', default='{}')
        parsed = self._parse_json(hydration_data, video_id)

        # This is necessary because the id of the author is not known in advance.
        # Will not raise an issue if no profile can be found as this is optional.
        author_info = try_get(parsed.get('profiles'), lambda x: list(x.values())[0], dict) or {}
        author_url = 'https://medal.tv/users/{}'.format(author_info.get('id')) if author_info.get('id') else None

        clip_info = try_get(parsed.get('clips'), lambda x: x.get(video_id), dict) or {}
        if(not clip_info):
            raise ExtractorError('Could not find video information.', video_id=video_id)

        if('error' in clip_info):
            if(clip_info.get('error') == 404):
                raise ExtractorError('That clip does not exist.', expected=True, video_id=video_id)
            else:
                raise ExtractorError('An unknown error occurred ({}).'.format(clip_info.get('error')), video_id=video_id)

        source_aspect_ratio = try_get(clip_info, lambda x: x.get('sourceWidth') / x.get('sourceHeight'), float) or (16 / 9)

        # ordered from worst to best quality
        heights = (144, 240, 360, 480, 720, 1080)

        formats = []
        thumbnails = []

        for height in heights:
            format_key = '{}p'.format(height)
            video_key = 'contentUrl{}'.format(format_key)
            thumbnail_key = 'thumbnail{}'.format(format_key)
            width = int(round(source_aspect_ratio * height))

            # Second condition needed as sometimes medal says
            # they have a format when in fact it is another format.
            if(video_key in clip_info and format_key in clip_info.get(video_key)):
                formats.append({
                    'url': clip_info.get(video_key),
                    'format_id': format_key,
                    'width': width,
                    'height': height
                })

            if(thumbnail_key in clip_info and format_key in clip_info.get(thumbnail_key)):
                thumbnails.append({
                    'id': format_key,
                    'url': clip_info.get(thumbnail_key),
                    'width': width,
                    'height': height
                })

        # add source to formats
        if('contentUrl' in clip_info):
            formats.append({
                'url': clip_info.get('contentUrl'),
                'format_id': 'source',
                'width': clip_info.get('sourceWidth'),
                'height': clip_info.get('sourceHeight')
            })

        return {
            'id': video_id,
            'title': clip_info.get('contentTitle'),
            'formats': formats,
            'thumbnails': thumbnails,
            'description': clip_info.get('contentDescription'),

            'uploader': author_info.get('displayName'),
            'timestamp': float_or_none(clip_info.get('created'), 1000),
            'uploader_id': author_info.get('id'),
            'uploader_url': author_url,

            'duration': float_or_none(clip_info.get('videoLengthSeconds')),
            'view_count': int_or_none(clip_info.get('views')),
            'like_count': int_or_none(clip_info.get('likes')),
            'comment_count': int_or_none(clip_info.get('comments'))
        }
