# coding: utf-8
from __future__ import unicode_literals

import json
from .common import InfoExtractor
from ..utils import (
    js_to_json,
    ExtractorError,
)
from ..compat import compat_urlparse


class UDNEmbedIE(InfoExtractor):
    IE_DESC = '聯合影音'
    _VALID_URL = r'https?://video\.udn\.com/(?:embed|play)/news/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://video.udn.com/embed/news/300040',
        'md5': 'de06b4c90b042c128395a88f0384817e',
        'info_dict': {
            'id': '300040',
            'ext': 'mp4',
            'title': '生物老師男變女 全校挺"做自己"',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }, {
        'url': 'https://video.udn.com/embed/news/300040',
        'only_matching': True,
    }, {
        # From https://video.udn.com/news/303776
        'url': 'https://video.udn.com/play/news/303776',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(url, video_id)

        options = json.loads(js_to_json(self._html_search_regex(
            r'var options\s*=\s*([^;]+);', page, 'video urls dictionary')))

        video_urls = options['video']

        if video_urls.get('youtube'):
            return self.url_result(video_urls.get('youtube'), 'Youtube')

        try:
            del video_urls['youtube']
        except KeyError:
            pass

        formats = [{
            'url': self._download_webpage(
                compat_urlparse.urljoin(url, api_url), video_id,
                'retrieve url for %s video' % video_type),
            'format_id': video_type,
            'preference': 0 if video_type == 'mp4' else -1,
        } for video_type, api_url in video_urls.items() if api_url]

        if not formats:
            raise ExtractorError('No videos found', expected=True)

        self._sort_formats(formats)

        thumbnail = None

        if options.get('gallery') and len(options['gallery']):
            thumbnail = options['gallery'][0].get('original')

        return {
            'id': video_id,
            'formats': formats,
            'title': options['title'],
            'thumbnail': thumbnail
        }
