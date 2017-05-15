# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class LibsynIE(InfoExtractor):
    _VALID_URL = r'(?P<mainurl>https?://html5-player\.libsyn\.com/embed/episode/id/(?P<id>[0-9]+))'

    _TESTS = [{
        'url': 'http://html5-player.libsyn.com/embed/episode/id/3377616/',
        'md5': '443360ee1b58007bc3dcf09b41d093bb',
        'info_dict': {
            'id': '3377616',
            'ext': 'mp3',
            'title': "The Daily Show Podcast without Jon Stewart - Episode 12: Bassem Youssef: Egypt's Jon Stewart",
            'description': 'md5:601cb790edd05908957dae8aaa866465',
            'upload_date': '20150220',
            'thumbnail': 're:^https?://.*',
        },
    }, {
        'url': 'https://html5-player.libsyn.com/embed/episode/id/3727166/height/75/width/200/theme/standard/direction/no/autoplay/no/autonext/no/thumbnail/no/preload/no/no_addthis/no/',
        'md5': '6c5cb21acd622d754d3b1a92b582ce42',
        'info_dict': {
            'id': '3727166',
            'ext': 'mp3',
            'title': 'Clients From Hell Podcast - How a Sex Toy Company Kickstarted my Freelance Career',
            'upload_date': '20150818',
            'thumbnail': 're:^https?://.*',
        }
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')
        url = m.group('mainurl')
        webpage = self._download_webpage(url, video_id)

        formats = [{
            'url': media_url,
        } for media_url in set(re.findall(r'var\s+mediaURL(?:Libsyn)?\s*=\s*"([^"]+)"', webpage))]

        podcast_title = self._search_regex(
            r'<h2>([^<]+)</h2>', webpage, 'podcast title', default=None)
        episode_title = self._search_regex(
            r'(?:<div class="episode-title">|<h3>)([^<]+)</', webpage, 'episode title')

        title = '%s - %s' % (podcast_title, episode_title) if podcast_title else episode_title

        description = self._html_search_regex(
            r'<div id="info_text_body">(.+?)</div>', webpage,
            'description', default=None)
        thumbnail = self._search_regex(
            r'<img[^>]+class="info-show-icon"[^>]+src="([^"]+)"',
            webpage, 'thumbnail', fatal=False)
        release_date = unified_strdate(self._search_regex(
            r'<div class="release_date">Released: ([^<]+)<', webpage, 'release date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': release_date,
            'formats': formats,
        }
