from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    int_or_none,
    js_to_json,
    mimetype2ext,
    ExtractorError,
)


class ImgurIE(InfoExtractor):
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/(?:(?:gallery|topic/[^/]+)/)?(?P<id>[a-zA-Z0-9]{6,})(?:[/?#&]+|\.[a-z]+)?$'

    _TESTS = [{
        'url': 'https://i.imgur.com/A61SaA1.gifv',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 'Imgur: The most awesome images on the Internet.',
        },
    }, {
        'url': 'https://imgur.com/A61SaA1',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 'Imgur: The most awesome images on the Internet.',
        },
    }, {
        'url': 'https://imgur.com/gallery/YcAQlkx',
        'info_dict': {
            'id': 'YcAQlkx',
            'ext': 'mp4',
            'title': 'Classic Steve Carell gif...cracks me up everytime....damn the repost downvotes....',
            'description': 'Imgur: The most awesome images on the Internet.'

        }
    }, {
        'url': 'http://imgur.com/topic/Funny/N8rOudd',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            compat_urlparse.urljoin(url, video_id), video_id)

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
            'description': self._og_search_description(webpage),
            'title': self._og_search_title(webpage),
        }


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
