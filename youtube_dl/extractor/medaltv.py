# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError


class MedalTVIE(InfoExtractor):
    _VALID_URL = r'(?:https://)?(?:www\.)?medal\.tv(?:/clips)?/(?P<id>[0-9]+)'
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

        url = 'https://medal.tv/clips/{}'.format(video_id)
        webpage = self._download_webpage(url, video_id)

        hydration_data = self._search_regex(r'<script>.*hydrationData\s*=\s*({.+?})\s*</script>', webpage, 'hydration data', default='{}')
        parsed = self._parse_json(hydration_data, video_id, fatal=False)

        author_info = next(iter(parsed['profiles'].values()))
        clip_info = parsed['clips'][video_id]

        if('error' in clip_info):
            if(clip_info['error'] == 404):
                raise ExtractorError('That clip does not exist.', expected=True, video_id=video_id)
            else:
                raise ExtractorError('An unknown error occurred ({}).'.format(clip_info['error']), video_id=video_id)
        source_aspect_ratio = clip_info['sourceWidth'] / clip_info['sourceHeight']

        # ordered from worst to best quality
        sizes = (144, 240, 360, 480, 720, 1080)

        formats = []
        thumbnails = []

        for size in sizes:
            format_key = '{}p'.format(size)
            video_key = 'contentUrl{}'.format(format_key)
            thumbnail_key = 'thumbnail{}'.format(format_key)

            # second condition needed as sometimes medal says
            # they have a format when in fact it is another format
            if(video_key in clip_info and format_key in clip_info[video_key]):
                formats.append({
                    'url': clip_info[video_key],
                    'format_id': format_key,
                    'width': round(source_aspect_ratio * size),
                    'height': size
                })

            if(thumbnail_key in clip_info and format_key in clip_info[thumbnail_key]):
                thumbnails.append({
                    'id': format_key,
                    'url': clip_info[thumbnail_key],
                    'width': round(source_aspect_ratio * size),
                    'height': size
                })

        formats.append({
            'url': clip_info['contentUrl'],
            'format_id': 'source',
            'width': clip_info['sourceWidth'],
            'height': clip_info['sourceHeight']
        })

        return {
            'id': video_id,
            'title': clip_info['contentTitle'] if clip_info['hasTitle'] else '',

            'formats': formats,
            'url': clip_info['contentUrl'],

            'thumbnails': thumbnails,
            'thumbnail': thumbnails[0]['url'],

            'description': clip_info['contentDescription'],

            # author information
            'uploader': author_info['displayName'],
            'timestamp': clip_info['created'] / 1000,
            'uploader_id': author_info['id'],
            'uploader_url': 'https://medal.tv/users/{}'.format(author_info['id']),

            # other clip information
            'duration': clip_info['videoLengthSeconds'],
            'view_count': clip_info['views'],
            'like_count': clip_info['likes'],
            'comment_count': clip_info['comments']
        }
