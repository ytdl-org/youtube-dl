# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class TVN24IE(InfoExtractor):
    _VALID_URL = r'http://(?:tvn24bis|(?:www|fakty)\.tvn24)\.pl/.+/(?P<id>[^/]+)\.html'
    _TEST = {
        'url': 'http://www.tvn24.pl/wiadomosci-z-kraju,3/oredzie-artura-andrusa,702428.html',
        'md5': 'fbdec753d7bc29d96036808275f2130c',
        'info_dict': {
            'id': '1584444',
            'ext': 'mp4',
            'title': '"Święta mają być wesołe, dlatego, ludziska, wszyscy pod jemiołę"',
            'description': 'Wyjątkowe orędzie Artura Andrusa, jednego z gości "Szkła kontaktowego".',
            'thumbnail': 're:http://.*[.]jpeg',
        }
    }

    def _real_extract(self, url):
        page_id = self._match_id(url)
        webpage = self._download_webpage(url, page_id)
        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)
        thumbnail = self._html_search_regex(r'\bdata-poster="(.+?)"', webpage, 'data-poster')
        share_params = self._html_search_regex(r'\bdata-share-params="(.+?)"', webpage, 'data-share-params')
        share_params = self._parse_json(share_params, page_id)
        video_id = share_params['id']
        quality_data = self._html_search_regex(r'\bdata-quality="(.+?)"', webpage, 'data-quality')
        quality_data = self._parse_json(quality_data, page_id)
        formats = []
        for format_id, url in quality_data.items():
            formats.append({
                'format_id': format_id,
                'height': int(format_id.rstrip('p')),
                'url': url,
                'ext': 'mp4',
            })
        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
