from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    mimetype2ext,
    ExtractorError,
)


class ImgurIE(InfoExtractor):
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/(?:(?:gallery|(?:topic|r)/[^/]+)/)?(?P<id>[a-zA-Z0-9]{6,})(?:[/?#&]+|\.[a-z0-9]+)?$'

    _TESTS = [{
        'url': 'https://i.imgur.com/A61SaA1.gifv',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 'Imgur: The magic of the Internet',
        },
    }, {
        'url': 'https://imgur.com/A61SaA1',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 'Imgur: The magic of the Internet',
        },
    }, {
        'url': 'https://imgur.com/gallery/YcAQlkx',
        'info_dict': {
            'id': 'YcAQlkx',
            'ext': 'mp4',
            'title': 'Classic Steve Carell gif...cracks me up everytime....damn the repost downvotes....',
        }
    }, {
        'url': 'http://imgur.com/topic/Funny/N8rOudd',
        'only_matching': True,
    }, {
        'url': 'http://imgur.com/r/aww/VQcQPhM',
        'only_matching': True,
    }, {
        'url': 'https://i.imgur.com/crGpqCV.mp4',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        gifv_url = 'https://i.imgur.com/{id}.gifv'.format(id=video_id)
        webpage = self._download_webpage(gifv_url, video_id)

        width = int_or_none(self._og_search_property(
            'video:width', webpage, default=None))
        height = int_or_none(self._og_search_property(
            'video:height', webpage, default=None))

        video_elements = self._search_regex(
            r'(?s)<div class="video-elements">(.*?)</div>',
            webpage, 'video elements', default=None)
        if not video_elements:
            raise ExtractorError(
                'No sources found for video %s. Maybe an image?' % video_id,
                expected=True)

        formats = []
        for m in re.finditer(r'<source\s+src="(?P<src>[^"]+)"\s+type="(?P<type>[^"]+)"', video_elements):
            formats.append({
                'format_id': m.group('type').partition('/')[2],
                'url': self._proto_relative_url(m.group('src')),
                'ext': mimetype2ext(m.group('type')),
                'acodec': 'none',
                'width': width,
                'height': height,
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })

        gif_json = self._search_regex(
            r'(?s)var\s+videoItem\s*=\s*(\{.*?\})',
            webpage, 'GIF code', fatal=False)
        if gif_json:
            gifd = self._parse_json(
                gif_json, video_id, transform_source=js_to_json)
            formats.append({
                'format_id': 'gif',
                'preference': -10,
                'width': width,
                'height': height,
                'ext': 'gif',
                'acodec': 'none',
                'vcodec': 'gif',
                'container': 'gif',
                'url': self._proto_relative_url(gifd['gifUrl']),
                'filesize': gifd.get('size'),
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'description': self._og_search_description(webpage, default=None),
            'title': self._og_search_title(webpage),
        }


class ImgurUnmutedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/t/unmuted/(?P<id>[a-zA-Z0-9]{6,})(?:[/?#&]+|\.[a-z]+)?$'

    _TESTS = [{
        'url': 'https://imgur.com/t/unmuted/6lAn9VQ',
        'info_dict': {
            'id': '6lAn9VQ',
        },
        'playlist_count': 3,
        'playlist': [
            {
                'info_dict': {
                    'id': '3inf5ZW-6lAn9VQ',
                    'ext': 'mp4',
                    'title': 're:Penguins !-3inf5ZW',
                    'description': 'Imgur: The magic of the Internet',
                }
            }, {
                'info_dict': {
                    'id': 'ejQsvLp-6lAn9VQ',
                    'ext': 'mp4',
                    'title': 're:Penguins !-ejQsvLp',
                    'description': 'Imgur: The magic of the Internet',
                }
            }, {
                'info_dict': {
                    'id': '3WRggtZ-6lAn9VQ',
                    'ext': 'mp4',
                    'title': 're:Penguins !-3WRggtZ',
                    'description': 'Imgur: The magic of the Internet',
                }
            },
        ]
    }, {
        'url': 'https://imgur.com/t/unmuted/kx2uD3C',
        'info_dict': {
            'id': 'kx2uD3C',
            'ext': 'mp4',
            'title': 're:Intruder$',
            'description': 'Imgur: The magic of the Internet',
        },
    }, {
        'url': 'https://imgur.com/t/unmuted/wXSK0YH',
        'info_dict': {
            'id': 'wXSK0YH',
            'ext': 'mp4',
            'title': 're:I got the blues$',
            'description': 'Imgur: The magic of the Internet',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_json = self._search_regex(
            r'image\s*:\s*({.*})',
            webpage, 'video json', default=None)

        videod = self._parse_json(video_json, video_id)
        album_images = videod.get('album_images')
        images = album_images.get('images')

        entries = []
        add_hash = False
        if len(images) > 1:
            add_hash = True

        for image in images:
            formats = []
            h = image.get('hash')
            url = 'https://i.imgur.com/{id}.mp4'.format(id=h)
            filetype = image.get('ext').lstrip('.')
            width = image.get('width')
            height = image.get('height')

            formats.append({
                'format_id': filetype,
                'url': url,
                'ext': filetype,
                'width': width,
                'height': height,
                'http_headers': {
                    'User-Agent': 'youtube-dl (like wget)',
                },
            })

            self._sort_formats(formats)
            title = self._og_search_title(webpage)
            indiv_video_id = video_id

            if add_hash:
                title += '-' + h
                indiv_video_id = h + '-' + video_id

            entries.append({
                'id': indiv_video_id,
                'formats': formats,
                'description': self._og_search_description(webpage, default=None),
                'title': title,
            })

        return self.playlist_result(entries, video_id)


class ImgurAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/(?:(?:a|gallery|topic/[^/]+)/)?(?P<id>[a-zA-Z0-9]{5})(?:[/?#&]+)?$'

    _TESTS = [{
        'url': 'http://imgur.com/gallery/Q95ko',
        'info_dict': {
            'id': 'Q95ko',
        },
        'playlist_count': 25,
    }, {
        'url': 'http://imgur.com/a/j6Orj',
        'only_matching': True,
    }, {
        'url': 'http://imgur.com/topic/Aww/ll5Vk',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        album_id = self._match_id(url)

        album_images = self._download_json(
            'http://imgur.com/gallery/%s/album_images/hit.json?all=true' % album_id,
            album_id, fatal=False)

        if album_images:
            data = album_images.get('data')
            if data and isinstance(data, dict):
                images = data.get('images')
                if images and isinstance(images, list):
                    entries = [
                        self.url_result('http://imgur.com/%s' % image['hash'])
                        for image in images if image.get('hash')]
                    return self.playlist_result(entries, album_id)

        # Fallback to single video
        return self.url_result('http://imgur.com/%s' % album_id, ImgurIE.ie_key())
