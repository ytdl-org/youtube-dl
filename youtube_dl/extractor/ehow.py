from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote


class EHowIE(InfoExtractor):
    IE_NAME = 'eHow'
    _VALID_URL = r'https?://(?:www\.)?ehow\.com/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.ehow.com/13718302/diy-colorful-abstract-art-coasters',
        'md5': '9809b4e3f115ae2088440bcb4efbf371',
        'info_dict': {
            'id': '13718302',
            'ext': 'flv',
            'title': 'DIY Colorful Abstract Art Coasters',
            'description': 'Not only are these colorful DIY polymer clay coasters super fun to make and practical to have around the house, they\'ll definitely exercise your artistic skills...',
            'uploader': 'Maya Marin',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_url = self._search_regex(
            r'(?:file|source)=(http[^\'"&]*)', webpage, 'video URL')
        final_url = compat_urllib_parse_unquote(video_url)
        uploader = self._html_search_meta('uploader', webpage)
        title = self._og_search_title(webpage).replace(' | eHow', '')

        return {
            'id': video_id,
            'url': final_url,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'uploader': uploader,
        }
