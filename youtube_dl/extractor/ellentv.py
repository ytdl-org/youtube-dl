# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
)


class EllenTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:ellentv|ellentube)\.com/videos/(?P<id>[a-z0-9_-]+)'
    _TESTS = [{
        'url': 'http://www.ellentv.com/videos/0-7jqrsr18/',
        'md5': 'e4af06f3bf0d5f471921a18db5764642',
        'info_dict': {
            'id': '0-7jqrsr18',
            'ext': 'mp4',
            'title': 'What\'s Wrong with These Photos? A Whole Lot',
            'description': 'md5:35f152dc66b587cf13e6d2cf4fa467f6',
            'timestamp': 1406876400,
            'upload_date': '20140801',
        }
    }, {
        'url': 'http://ellentube.com/videos/0-dvzmabd5/',
        'md5': '98238118eaa2bbdf6ad7f708e3e4f4eb',
        'info_dict': {
            'id': '0-dvzmabd5',
            'ext': 'mp4',
            'title': '1 year old twin sister makes her brother laugh',
            'description': '1 year old twin sister makes her brother laugh',
            'timestamp': 1419542075,
            'upload_date': '20141225',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        video_url = self._html_search_meta('VideoURL', webpage, 'url')
        title = self._og_search_title(webpage, default=None) or self._search_regex(
            r'pageName\s*=\s*"([^"]+)"', webpage, 'title')
        description = self._html_search_meta(
            'description', webpage, 'description') or self._og_search_description(webpage)
        timestamp = parse_iso8601(self._search_regex(
            r'<span class="publish-date"><time datetime="([^"]+)">',
            webpage, 'timestamp'))

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'timestamp': timestamp,
        }


class EllenTVClipsIE(InfoExtractor):
    IE_NAME = 'EllenTV:clips'
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/episodes/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/episodes/meryl-streep-vanessa-hudgens/',
        'info_dict': {
            'id': 'meryl-streep-vanessa-hudgens',
            'title': 'Meryl Streep, Vanessa Hudgens',
        },
        'playlist_mincount': 9,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)
        playlist = self._extract_playlist(webpage)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': self._og_search_title(webpage),
            'entries': self._extract_entries(playlist)
        }

    def _extract_playlist(self, webpage):
        json_string = self._search_regex(r'playerView.addClips\(\[\{(.*?)\}\]\);', webpage, 'json')
        try:
            return json.loads("[{" + json_string + "}]")
        except ValueError as ve:
            raise ExtractorError('Failed to download JSON', cause=ve)

    def _extract_entries(self, playlist):
        return [self.url_result(item['url'], 'EllenTV') for item in playlist]
