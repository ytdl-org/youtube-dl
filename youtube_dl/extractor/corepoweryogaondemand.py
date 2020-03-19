# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
)


class CorePowerYogaOnDemandIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?corepoweryogaondemand\.com/keep-up-your-practice/videos/(?P<id>[-a-zA-Z0-9]+)'
    _TEST = {
        'url': 'https://www.corepoweryogaondemand.com/keep-up-your-practice/videos/trust-the-unknown',
        'md5': 'b29716154060ddbf2defb7cd9a11492e',
        'info_dict': {
            'id': 'trust-the-unknown',
            'ext': 'mp4',
            'title': 'Trust the Unknown',
            'description': 'Trust in the infinite unknown and let your breath guide you.'
        }
    }

    def _extract_format(self, raw_format):
        return {
            'url': raw_format['url'],
            'height': raw_format.get('height'),
            'width': raw_format.get('width'),
            'fps': raw_format.get('fps'),
            'resolution': raw_format.get('quality')
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>([^<]+) - [^<]+ - [^<]+</title>', webpage, 'title', default=None)

        # extract iframe
        iframe_url = self._search_regex(r'<iframe[^>]+src=\"https://embed\.vhx\.tv/(?P<url>[^\"]+)\"', webpage, 'embedded video iframe', group="url")
        iframe = self._download_webpage('https://embed.vhx.tv/' + iframe_url, 'Fetch embedded video')

        # vimeo config URL
        ott_data = self._search_regex(r'window\.OTTData\s*=\s*(?P<json>{.+})', iframe, 'video metadata', group="json")
        video_metadata = self._parse_json(ott_data, video_id)
        vimeo_url = video_metadata['config_url']

        # fetch media from config URL
        video_config = self._parse_json(self._download_webpage(vimeo_url, 'Fetch media information'), video_id)
        raw_formats = video_config['request']['files']['progressive']
        formats = [self._extract_format(i) for i in raw_formats]
        sorted_formats = sorted(formats, key=lambda i: int_or_none(i['resolution'][:-1]))

        return {
            'id': video_id,
            'title': title,
            'formats': sorted_formats,
            'description': self._og_search_description(webpage, default=None),
        }
