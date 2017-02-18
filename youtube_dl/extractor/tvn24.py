# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unescapeHTML,
)


class TVN24IE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:[^/]+)\.)?tvn24(?:bis)?\.pl/(?:[^/]+/)*(?P<id>[^/]+)\.html'
    _TESTS = [{
        'url': 'http://www.tvn24.pl/wiadomosci-z-kraju,3/oredzie-artura-andrusa,702428.html',
        'md5': 'fbdec753d7bc29d96036808275f2130c',
        'info_dict': {
            'id': '1584444',
            'ext': 'mp4',
            'title': '"Święta mają być wesołe, dlatego, ludziska, wszyscy pod jemiołę"',
            'description': 'Wyjątkowe orędzie Artura Andrusa, jednego z gości "Szkła kontaktowego".',
            'thumbnail': 're:http://.*[.]jpeg',
        }
    }, {
        'url': 'http://fakty.tvn24.pl/ogladaj-online,60/53-konferencja-bezpieczenstwa-w-monachium,716431.html',
        'only_matching': True,
    }, {
        'url': 'http://sport.tvn24.pl/pilka-nozna,105/ligue-1-kamil-glik-rozcial-glowe-monaco-tylko-remisuje-z-bastia,716522.html',
        'only_matching': True,
    }, {
        'url': 'http://tvn24bis.pl/poranek,146,m/gen-koziej-w-tvn24-bis-wracamy-do-czasow-zimnej-wojny,715660.html',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage)

        def extract_json(attr, name, fatal=True):
            return self._parse_json(
                self._search_regex(
                    r'\b%s=(["\'])(?P<json>(?!\1).+?)\1' % attr, webpage,
                    name, group='json', fatal=fatal) or '{}',
                video_id, transform_source=unescapeHTML, fatal=fatal)

        quality_data = extract_json('data-quality', 'formats')

        formats = []
        for format_id, url in quality_data.items():
            formats.append({
                'url': url,
                'format_id': format_id,
                'height': int_or_none(format_id.rstrip('p')),
            })
        self._sort_formats(formats)

        description = self._og_search_description(webpage)
        thumbnail = self._og_search_thumbnail(
            webpage, default=None) or self._html_search_regex(
            r'\bdata-poster=(["\'])(?P<url>(?!\1).+?)\1', webpage,
            'thumbnail', group='url')

        share_params = extract_json(
            'data-share-params', 'share params', fatal=False)
        if isinstance(share_params, dict):
            video_id = share_params.get('id') or video_id

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
