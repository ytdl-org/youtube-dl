# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    traverse_obj,
)

class CallinIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?callin\.com/episode/(?:[^/#?-]+-)*(?P<id>[^/#?-]+)'
    _TESTS = [{
        'url': 'https://www.callin.com/episode/fcc-commissioner-brendan-carr-on-elons-PrumRdSQJW',
        'md5': '2b17390cd9f80fc3cac530883f6e3d6e',
        'info_dict': {
            'id': 'PrumRdSQJW',
            'ext': 'mp4',
            'title': 'FCC Commissioner Brendan Carr on Elon’s Starlink',
            'description': 'Or, why the government doesn’t like SpaceX',
        }
    }, {
        'url': 'https://www.callin.com/episode/episode-81-elites-melt-down-over-student-debt-lzxMidUnjA',
        'md5': 'bd6d6b762e0d5c20cd6090e3d27534a8',
        'info_dict': {
            'id': 'lzxMidUnjA',
            'ext': 'mp4',
            'title': 'Episode 81- Elites MELT DOWN over Student Debt Victory? Rumble in NYC?',
            'description': 'Let’s talk todays episode about the primary election shake up in NYC and the elites melting down over student debt cancelation.',
        }
    }]

    def _search_nextjs_data(self, webpage, video_id, *, transform_source=None, fatal=True, **kw):
        return self._parse_json(
            self._search_regex(
                r'(?s)<script[^>]+id=[\'"]__NEXT_DATA__[\'"][^>]*>([^<]+)</script>',
                webpage, 'next.js data', fatal=fatal, **kw),
            video_id, transform_source=transform_source, fatal=fatal)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        # webpage_json = self._download_json(url, video_id)

        next_data = self._search_nextjs_data(webpage, video_id)
        valid = traverse_obj(next_data, ('props', 'pageProps', 'episode'))
        if not valid:
            raise ExtractorError('Failed to find m3u8')
        
        episode = self._search_nextjs_data(webpage, video_id)['props']['pageProps']['episode']
        title = episode.get('title')
        if not title:
            title = self._og_search_title(webpage)
        description = episode.get('description')
        if not description:
            description = self._og_search_description(webpage)
        
        video_url = episode.get('m3u8')
        formats = self._extract_m3u8_formats(
            video_url, video_id, 'mp4')
        self._sort_formats(formats)

        

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
        }