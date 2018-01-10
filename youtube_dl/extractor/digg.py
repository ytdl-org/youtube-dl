from __future__ import unicode_literals

from .common import InfoExtractor


class DiggIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?digg\.com/video/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://digg.com/video/sci-fi-short-jonah-daniel-kaluuya-get-out',
        'info_dict': {
            'id': 'LcqvmS0b',
            'ext': 'mp4',
            'title': "'Get Out' Star Daniel Kaluuya Goes On 'Moby Dick'-Like Journey In Sci-Fi Short 'Jonah'",
            'description': 'md5:541bb847648b6ee3d6514bc84b82efda',
            'upload_date': '20180109',
            'timestamp': 1515530551,
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        jwplatform_id = self._search_regex(
            r'video_id\s*:\s*["\']([a-zA-Z0-9]{8})', webpage, 'jwplatform id',
            default=None)

        if not jwplatform_id:
            return self.url_result(url, 'Generic')

        return {
            '_type': 'url_transparent',
            'ie_key': 'JWPlatform',
            'url': 'jwplatform:%s' % jwplatform_id,
            'id': jwplatform_id,
            'display_id': display_id,
        }
