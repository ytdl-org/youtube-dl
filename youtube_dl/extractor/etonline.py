# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class ETOnlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?etonline\.com/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://www.etonline.com/tv/211130_dove_cameron_liv_and_maddie_emotional_episode_series_finale/',
        'info_dict': {
            'id': '211130_dove_cameron_liv_and_maddie_emotional_episode_series_finale',
            'title': 'md5:a21ec7d3872ed98335cbd2a046f34ee6',
            'description': 'md5:8b94484063f463cca709617c79618ccd',
        },
        'playlist_count': 2,
    }, {
        'url': 'http://www.etonline.com/media/video/here_are_the_stars_who_love_bringing_their_moms_as_dates_to_the_oscars-211359/',
        'only_matching': True,
    }]
    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/1242911076001/default_default/index.html?videoId=ref:%s'

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = [
            self.url_result(
                self.BRIGHTCOVE_URL_TEMPLATE % video_id, 'BrightcoveNew', video_id)
            for video_id in re.findall(
                r'site\.brightcove\s*\([^,]+,\s*["\'](title_\d+)', webpage)]

        return self.playlist_result(
            entries, playlist_id,
            self._og_search_title(webpage, fatal=False),
            self._og_search_description(webpage))
