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
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/(?!gallery)(?P<id>[a-zA-Z0-9]+)'

    _TESTS = [{
        'url': 'https://i.imgur.com/A61SaA1.gifv',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 're:The origin of the Internet\'s most viral images$|The Internet\'s visual storytelling community\. Explore, share, and discuss the best visual stories the Internet has to offer\.$',
        },
    }, {
        'url': 'https://imgur.com/A61SaA1',
        'info_dict': {
            'id': 'A61SaA1',
            'ext': 'mp4',
            'title': 're:Imgur GIF$|MRW gifv is up and running without any bugs$',
            'description': 're:The origin of the Internet\'s most viral images$|The Internet\'s visual storytelling community\. Explore, share, and discuss the best visual stories the Internet has to offer\.$',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            compat_urlparse.urljoin(url, video_id), video_id)

        width = int_or_none(self._search_regex(
            r'<param name="width" value="([0-9]+)"',
            webpage, 'width', fatal=False))
        height = int_or_none(self._search_regex(
            r'<param name="height" value="([0-9]+)"',
            webpage, 'height', fatal=False))

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
    _VALID_URL = r'https?://(?:i\.)?imgur\.com/gallery/(?P<id>[a-zA-Z0-9]+)'

    _TEST = {
        'url': 'http://imgur.com/gallery/Q95ko',
        'info_dict': {
            'id': 'Q95ko',
        },
        'playlist_count': 25,
    }

    def _real_extract(self, url):
        album_id = self._match_id(url)

        album_images = self._download_json(
            'http://imgur.com/gallery/%s/album_images/hit.json?all=true' % album_id,
            album_id)['data']['images']

        entries = [
            self.url_result('http://imgur.com/%s' % image['hash'])
            for image in album_images if image.get('hash')]

        return self.playlist_result(entries, album_id)
