# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    parse_duration,
    int_or_none,
)


class ChirbitIE(InfoExtractor):
    IE_NAME = 'chirbit'
    _VALID_URL = r'https?://(?:www\.)?chirb\.it/(?:(?:wp|pl)/|fb_chirbit_player\.swf\?key=)?(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'http://chirb.it/PrIPv5',
        'md5': '9847b0dad6ac3e074568bf2cfb197de8',
        'info_dict': {
            'id': 'PrIPv5',
            'ext': 'mp3',
            'title': 'Фасадстрой',
            'duration': 52,
            'view_count': int,
            'comment_count': int,
        }
    }, {
        'url': 'https://chirb.it/fb_chirbit_player.swf?key=PrIPv5',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://chirb.it/%s' % audio_id, audio_id)

        audio_url = self._search_regex(
            r'"setFile"\s*,\s*"([^"]+)"', webpage, 'audio url')

        title = self._search_regex(
            r'itemprop="name">([^<]+)', webpage, 'title')
        duration = parse_duration(self._html_search_meta(
            'duration', webpage, 'duration', fatal=False))
        view_count = int_or_none(self._search_regex(
            r'itemprop="playCount"\s*>(\d+)', webpage,
            'listen count', fatal=False))
        comment_count = int_or_none(self._search_regex(
            r'>(\d+) Comments?:', webpage,
            'comment count', fatal=False))

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
        }


class ChirbitProfileIE(InfoExtractor):
    IE_NAME = 'chirbit:profile'
    _VALID_URL = r'https?://(?:www\.)?chirbit.com/(?:rss/)?(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://chirbit.com/ScarletBeauty',
        'info_dict': {
            'id': 'ScarletBeauty',
            'title': 'Chirbits by ScarletBeauty',
        },
        'playlist_mincount': 3,
    }

    def _real_extract(self, url):
        profile_id = self._match_id(url)

        rss = self._download_xml(
            'http://chirbit.com/rss/%s' % profile_id, profile_id)

        entries = [
            self.url_result(audio_url.text, 'Chirbit')
            for audio_url in rss.findall('./channel/item/link')]

        title = rss.find('./channel/title').text

        return self.playlist_result(entries, profile_id, title)
