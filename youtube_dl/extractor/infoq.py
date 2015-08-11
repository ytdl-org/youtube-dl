from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_urlparse,
)


class InfoQIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?infoq\.com/(?:[^/]+/)+(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.infoq.com/presentations/A-Few-of-My-Favorite-Python-Things',
        'md5': 'b5ca0e0a8c1fed93b0e65e48e462f9a2',
        'info_dict': {
            'id': '12-jan-pythonthings',
            'ext': 'mp4',
            'description': 'Mike Pirnat presents some tips and tricks, standard libraries and third party packages that make programming in Python a richer experience.',
            'title': 'A Few of My Favorite [Python] Things',
        },
    }, {
        'url': 'http://www.infoq.com/fr/presentations/changez-avis-sur-javascript',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        video_description = self._html_search_meta('description', webpage, 'description')

        # The server URL is hardcoded
        video_url = 'rtmpe://video.infoq.com/cfx/st/'

        # Extract video URL
        encoded_id = self._search_regex(
            r"jsclassref\s*=\s*'([^']*)'", webpage, 'encoded id')
        real_id = compat_urllib_parse_unquote(base64.b64decode(encoded_id.encode('ascii')).decode('utf-8'))
        playpath = 'mp4:' + real_id

        video_filename = playpath.split('/')[-1]
        video_id, extension = video_filename.split('.')

        http_base = self._search_regex(
            r'EXPRESSINSTALL_SWF\s*=\s*[^"]*"((?:https?:)?//[^/"]+/)', webpage,
            'HTTP base URL')

        formats = [{
            'format_id': 'rtmp',
            'url': video_url,
            'ext': extension,
            'play_path': playpath,
        }, {
            'format_id': 'http',
            'url': compat_urlparse.urljoin(url, http_base) + real_id,
        }]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'formats': formats,
        }
