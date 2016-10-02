# coding: utf-8
from __future__ import unicode_literals

import base64

from .common import InfoExtractor
from ..utils import parse_duration


class ChirbitIE(InfoExtractor):
    IE_NAME = 'chirbit'
    _VALID_URL = r'https?://(?:www\.)?chirb\.it/(?:(?:wp|pl)/|fb_chirbit_player\.swf\?key=)?(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'http://chirb.it/be2abG',
        'info_dict': {
            'id': 'be2abG',
            'ext': 'mp3',
            'title': 'md5:f542ea253f5255240be4da375c6a5d7e',
            'description': 'md5:f24a4e22a71763e32da5fed59e47c770',
            'duration': 306,
        },
        'params': {
            'skip_download': True,
        }
    }, {
        'url': 'https://chirb.it/fb_chirbit_player.swf?key=PrIPv5',
        'only_matching': True,
    }, {
        'url': 'https://chirb.it/wp/MN58c2',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        audio_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://chirb.it/%s' % audio_id, audio_id)

        data_fd = self._search_regex(
            r'data-fd=(["\'])(?P<url>(?:(?!\1).)+)\1',
            webpage, 'data fd', group='url')

        # Reverse engineered from https://chirb.it/js/chirbit.player.js (look
        # for soundURL)
        audio_url = base64.b64decode(
            data_fd[::-1].encode('ascii')).decode('utf-8')

        title = self._search_regex(
            r'class=["\']chirbit-title["\'][^>]*>([^<]+)', webpage, 'title')
        description = self._search_regex(
            r'<h3>Description</h3>\s*<pre[^>]*>([^<]+)</pre>',
            webpage, 'description', default=None)
        duration = parse_duration(self._search_regex(
            r'class=["\']c-length["\'][^>]*>([^<]+)',
            webpage, 'duration', fatal=False))

        return {
            'id': audio_id,
            'url': audio_url,
            'title': title,
            'description': description,
            'duration': duration,
        }


class ChirbitProfileIE(InfoExtractor):
    IE_NAME = 'chirbit:profile'
    _VALID_URL = r'https?://(?:www\.)?chirbit\.com/(?:rss/)?(?P<id>[^/]+)'
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
