# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_iso8601,
)


class EllenTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/videos/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/videos/0-7jqrsr18/',
        'md5': 'e4af06f3bf0d5f471921a18db5764642',
        'info_dict': {
            'id': '0-7jqrsr18',
            'ext': 'mp4',
            'title': 'What\'s Wrong with These Photos? A Whole Lot',
            'timestamp': 1406876400,
            'upload_date': '20140801',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        timestamp = parse_iso8601(self._search_regex(
            r'<span class="publish-date"><time datetime="([^"]+)">',
            webpage, 'timestamp'))

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'url': self._html_search_meta('VideoURL', webpage, 'url'),
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
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('id')

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
