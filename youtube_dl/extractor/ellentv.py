# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class EllenTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:ellentv|ellentube)\.com/videos/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/videos/0-ipq1gsai/',
        'md5': '4294cf98bc165f218aaa0b89e0fd8042',
        'info_dict': {
            'id': '0_ipq1gsai',
            'ext': 'mov',
            'title': 'Fast Fingers of Fate',
            'description': 'md5:3539013ddcbfa64b2a6d1b38d910868a',
            'timestamp': 1428035648,
            'upload_date': '20150403',
            'uploader_id': 'batchUser',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://widgets.ellentube.com/videos/%s' % video_id,
            video_id)

        partner_id = self._search_regex(
            r"var\s+partnerId\s*=\s*'([^']+)", webpage, 'partner id')

        kaltura_id = self._search_regex(
            [r'id="kaltura_player_([^"]+)"',
             r"_wb_entry_id\s*:\s*'([^']+)",
             r'data-kaltura-entry-id="([^"]+)'],
            webpage, 'kaltura id')

        return self.url_result('kaltura:%s:%s' % (partner_id, kaltura_id), 'Kaltura')


class EllenTVClipsIE(InfoExtractor):
    IE_NAME = 'EllenTV:clips'
    _VALID_URL = r'https?://(?:www\.)?ellentv\.com/episodes/(?P<id>[a-z0-9_-]+)'
    _TEST = {
        'url': 'http://www.ellentv.com/episodes/meryl-streep-vanessa-hudgens/',
        'info_dict': {
            'id': 'meryl-streep-vanessa-hudgens',
            'title': 'Meryl Streep, Vanessa Hudgens',
        },
        'playlist_mincount': 7,
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
            return json.loads('[{' + json_string + '}]')
        except ValueError as ve:
            raise ExtractorError('Failed to download JSON', cause=ve)

    def _extract_entries(self, playlist):
        return [
            self.url_result(
                'kaltura:%s:%s' % (item['kaltura_partner_id'], item['kaltura_entry_id']),
                'Kaltura')
            for item in playlist]
