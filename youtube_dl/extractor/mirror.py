# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    ExtractorError,
    RegexNotFoundError,
)

import re


class MirrorIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mirror\.co\.uk.*/(?P<id>[^/?#&]+)'

    _TEST = {
        'url': 'http://www.mirror.co.uk/news/uk-news/grenfell-tower-block-fire-london-10619120?service=responsive',
        'md5': 'e8c52bcdf5180884b4e4d3159de3a40b',
        'info_dict': {
            'id': '5470567455001',
            'ext': 'mp4',
            'title': 'Blaze at Grenfell Tower continues 11 hours on',
            'timestamp': 1497433370,
            'upload_date': '20170614',
            'uploader_id': '4221396001',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        title = None
        account_id = None
        video_id = None
        player_id = None

        try:
            json_data = self._parse_json(self._html_search_regex(
                r'<div[^>]+class=(["\'])json-placeholder\1[^>]+data-json=\1(?P<json>.*?)\1',
                webpage, 'extract json', group='json', fatal=False
            ), display_id, fatal=False)

            if all(k in json_data for k in ('playerData', 'videoData')):
                player_id = json_data['playerData'].get('playerId')
                account_id = json_data['playerData'].get('account')
                video_id = json_data['videoData'].get('videoId')
                title = json_data['videoData'].get('videoTitle')
            else:
                raise ExtractorError('json data not found')
        except (RegexNotFoundError, ExtractorError):
            title = self._og_search_title(
                webpage, default=None) or self._search_regex(
                r'<title>([^<]+)', webpage,
                'title', default=None)
            account_id = self._html_search_regex(
                r'<meta[^<]+?property=[\'"]+videoUrl[\'"]+.+?content=[\'"].+?brightcove\.com/\d+/(?P<account_id>[^/]+)/',
                webpage, 'account id', group='account_id'
            )
            video_id = self._html_search_regex(
                r'<meta[^<]+?property=[\'"]+videoUrl[\'"]+.+?content=[\'"].+?brightcove\.com/[a-zA-Z0-9-_/]+_(?P<video_id>\d+)\.mp4',
                webpage, 'video id', group='video_id'
            )

        try:
            return {
                '_type': 'url_transparent',
                'id': video_id,
                'display_id': display_id,
                'url': 'http://players.brightcove.net/%s/%s_default/index.html?videoId=%s' % (account_id, player_id, video_id),
                'ie_key': 'BrightcoveNew'
            }
        except ExtractorError:
            return {
                'id': video_id,
                'title': title,
                'url': self._search_regex(
                    r'<meta[^<]+?property=[\'"]+videoUrl[\'"]+.+?content=[\'"](?P<video_url>.+?brightcove\.com\/[^\'"]+)',
                    webpage, 'video url', group='video_url'
                ),
                'uploader_id': account_id
            }
