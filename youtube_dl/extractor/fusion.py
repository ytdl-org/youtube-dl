from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, int_or_none


class FusionIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?fusion\.(?:net|tv)/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://fusion.tv/video/201781/u-s-and-panamanian-forces-work-together-to-stop-a-vessel-smuggling-drugs/',
        'info_dict': {
            'id': '0eaph8eeMwQ',
            'ext': 'mp4',
            'title': 'U.S. and Panamanian forces work together to stop a vessel smuggling drugs',
            'description': 'md5:0cc84a9943c064c0f46b128b41b1b0d7',
            'uploader': 'FUSION',
            'uploader_id': 'thisisfusion',
            'upload_date': '20150918'
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Youtube'],
    }, {
        'url': 'http://fusion.tv/video/201781',
        'only_matching': True,
    }, {
        'url': 'https://fusion.tv/video/584520/dreaming-of-the-whitest-christmas/',
        'info_dict': {
            'id': '584520',
            'ext': 'm3u8',
            'title': 'Dreaming of the Whitest Christmas',
            'description': 'md5:350a32da86dc05a2179c9694d9d61feb',
            'release_date': '20171211',
            'thumbnail': r're:http.*.jpg[?]?',
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        fusionData = self._parse_json(
            self._search_regex(
                r'(?si)fusionData\s*=\s*({.*?});', webpage,
                'fusionData'),
            display_id)

        data = fusionData.get('single')

        info = {
            'id': display_id,
            'title': data.get('title'),
            'display_id': data.get('slug'),
            'description': data.get('excerpt'),
        }

        published = data.get('published')
        if published and 'T' in published:
            info['release_date'] = published.split('T')[0].replace('-', '')

        if 'images' in data:
            info['thumbnails'] = [{'id': image, 'url': url} for image, url in data.get('images').items()]

        srcs = data.get('src')

        if not srcs:
            youtube_id = data.get('video_ids').get('youtube')
            if not youtube_id:
                raise ExtractorError('Could not find alternate youtube url')

            info['_type'] = 'url'
            info['url'] = youtube_id
            info['ie_key'] = 'Youtube'
            return info

        formats = []
        for format in srcs.keys():
            if format not in ['m3u8-hp-v3', 'm3u8-variant', 'mp4']:
                continue

            for vid in srcs.get(format).values():
                formats.append(
                    {
                        'url': vid.get('url'),
                        'width': int_or_none(vid.get('width')),
                        'height': int_or_none(vid.get('height')),
                        'format_note': vid.get('type').split('/')[1],
                        'protocol': 'm3u8' if format.startswith('m3u8') else None,
                        'quality': int_or_none(vid.get('width', 0)) * int_or_none(vid.get('height', 0))
                    }
                )

        formats.sort(key=lambda format: format['quality'])
        info['formats'] = formats
        return info
