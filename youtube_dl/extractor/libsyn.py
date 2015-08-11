# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class LibsynIE(InfoExtractor):
    _VALID_URL = r'https?://html5-player\.libsyn\.com/embed/episode/id/(?P<id>[0-9]+)'

    _TEST = {
        'url': 'http://html5-player.libsyn.com/embed/episode/id/3377616/',
        'md5': '443360ee1b58007bc3dcf09b41d093bb',
        'info_dict': {
            'id': '3377616',
            'ext': 'mp3',
            'title': "The Daily Show Podcast without Jon Stewart - Episode 12: Bassem Youssef: Egypt's Jon Stewart",
            'description': 'md5:601cb790edd05908957dae8aaa866465',
            'upload_date': '20150220',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = [{
            'url': media_url,
        } for media_url in set(re.findall('var\s+mediaURL(?:Libsyn)?\s*=\s*"([^"]+)"', webpage))]

        podcast_title = self._search_regex(
            r'<h2>([^<]+)</h2>', webpage, 'title')
        episode_title = self._search_regex(
            r'<h3>([^<]+)</h3>', webpage, 'title', default=None)

        title = '%s - %s' % (podcast_title, episode_title) if podcast_title else episode_title

        description = self._html_search_regex(
            r'<div id="info_text_body">(.+?)</div>', webpage,
            'description', fatal=False)

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
