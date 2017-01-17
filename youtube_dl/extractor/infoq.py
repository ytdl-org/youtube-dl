# coding: utf-8

from __future__ import unicode_literals

import base64

from ..compat import (
    compat_urllib_parse_unquote,
    compat_urlparse,
)
from ..utils import determine_ext
from .bokecc import BokeCCBaseIE


class InfoQIE(BokeCCBaseIE):
    _VALID_URL = r'https?://(?:www\.)?infoq\.com/(?:[^/]+/)+(?P<id>[^/]+)'

    _TESTS = [{
        'url': 'http://www.infoq.com/presentations/A-Few-of-My-Favorite-Python-Things',
        'md5': 'b5ca0e0a8c1fed93b0e65e48e462f9a2',
        'info_dict': {
            'id': 'A-Few-of-My-Favorite-Python-Things',
            'ext': 'mp4',
            'description': 'Mike Pirnat presents some tips and tricks, standard libraries and third party packages that make programming in Python a richer experience.',
            'title': 'A Few of My Favorite [Python] Things',
        },
    }, {
        'url': 'http://www.infoq.com/fr/presentations/changez-avis-sur-javascript',
        'only_matching': True,
    }, {
        'url': 'http://www.infoq.com/cn/presentations/openstack-continued-delivery',
        'md5': '4918d0cca1497f2244572caf626687ef',
        'info_dict': {
            'id': 'openstack-continued-delivery',
            'title': 'OpenStack持续交付之路',
            'ext': 'flv',
            'description': 'md5:308d981fb28fa42f49f9568322c683ff',
        },
    }]

    def _extract_rtmp_video(self, webpage):
        # The server URL is hardcoded
        video_url = 'rtmpe://video.infoq.com/cfx/st/'

        # Extract video URL
        encoded_id = self._search_regex(
            r"jsclassref\s*=\s*'([^']*)'", webpage, 'encoded id', default=None)

        real_id = compat_urllib_parse_unquote(base64.b64decode(encoded_id.encode('ascii')).decode('utf-8'))
        playpath = 'mp4:' + real_id

        return [{
            'format_id': 'rtmp_video',
            'url': video_url,
            'ext': determine_ext(playpath),
            'play_path': playpath,
        }]

    def _extract_cookies(self, webpage):
        policy = self._search_regex(r'InfoQConstants.scp\s*=\s*\'([^\']+)\'', webpage, 'policy')
        signature = self._search_regex(r'InfoQConstants.scs\s*=\s*\'([^\']+)\'', webpage, 'signature')
        key_pair_id = self._search_regex(r'InfoQConstants.sck\s*=\s*\'([^\']+)\'', webpage, 'key-pair-id')
        return 'CloudFront-Policy=%s; CloudFront-Signature=%s; CloudFront-Key-Pair-Id=%s' % (
            policy, signature, key_pair_id)

    def _extract_http_video(self, webpage):
        http_video_url = self._search_regex(r'P\.s\s*=\s*\'([^\']+)\'', webpage, 'video URL')
        return [{
            'format_id': 'http_video',
            'url': http_video_url,
            'ext': determine_ext(http_video_url),
            'http_headers': {
                'Cookie': self._extract_cookies(webpage)
            },
        }]

    def _extract_http_audio(self, webpage):
        http_audio_url = self._search_regex(r'<input[^>]*?name="filename"[^>]*?value="([^\"]+)"[^>]*?>', webpage, 'audio URL', fatal=False)
        if http_audio_url is None:
            return []
        http_audio_url = compat_urlparse.urljoin('http://res.infoq.com/downloads/mp3downloads/', http_audio_url)

        return [{
            'format_id': 'http_audio',
            'url': http_audio_url,
            'ext': determine_ext(http_audio_url, ""),
            'vcodec': 'none',
            'http_headers': {
                'Cookie': self._extract_cookies(webpage)
            },
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        video_description = self._html_search_meta('description', webpage, 'description')

        if '/cn/' in url:
            # for China videos, HTTP video URL exists but always fails with 403
            formats = self._extract_bokecc_formats(webpage, video_id)
        else:
            formats = (
                self._extract_rtmp_video(webpage) +
                self._extract_http_video(webpage) +
                self._extract_http_audio(webpage))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'description': video_description,
            'formats': formats,
        }
