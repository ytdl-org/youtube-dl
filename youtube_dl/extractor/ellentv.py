# coding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor, ExtractorError

class EllenTVIE(InfoExtractor):
    IE_NAME = u'ellentv'
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/videos/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/videos/0-7jqrsr18/',
        'md5': 'e4af06f3bf0d5f471921a18db5764642',
        'info_dict': {
            'id': '0-7jqrsr18',
            'ext': 'mp4',
            'title': u'What\'s Wrong with These Photos? A Whole Lot',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        id = mobj.group('id')

        webpage = self._download_webpage(url, id)

        return {
            'id': id,
            'title': self._og_search_title(webpage),
            'url': self._html_search_meta('VideoURL', webpage, 'url')
        }

class EllenTVClipsIE(InfoExtractor):
    IE_NAME = u'ellentv:clips'
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/episodes/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/episodes/meryl-streep-vanessa-hudgens/',
        'md5': 'TODO: md5 sum of the first 10KiB of the video file',
        'info_dict': {
            'id': '0_wf6pizq7',
            'ext': 'mp4',
            'title': 'Video title goes here',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
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
        return [self.url_result(item[u'url'], 'EllenTV') for item in playlist]
