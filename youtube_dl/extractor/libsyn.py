# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import unified_strdate


class LibsynIE(InfoExtractor):
    _VALID_URL = r'(?P<mainurl>https?://html5-player\.libsyn\.com/embed/episode/id/(?P<id>[0-9]+))'

    _TESTS = [{
        'url': 'http://html5-player.libsyn.com/embed/episode/id/6324076/',
        'md5': '5b497505660690028d482f9a28431cca',
        'info_dict': {
            'id': '6324076',
            'ext': 'mp3',
            'title': "Verily, Octopi Sing - Pandas are not smallpox",
            'description': 'md5:0d20ad472ae296f22a0c9df23a6d78f1',
            'upload_date': '20180303',
            'thumbnail': 're:^https?://.*',
        },
    }, {
        'url': 'https://html5-player.libsyn.com/embed/episode/id/3727166/height/75/width/200/theme/standard/direction/no/autoplay/no/autonext/no/thumbnail/no/preload/no/no_addthis/no/',
        'md5': '6c5cb21acd622d754d3b1a92b582ce42',
        'info_dict': {
            'id': '3727166',
            'ext': 'mp3',
            'title': 'Clients From Hell Podcast - How a Sex Toy Company Kickstarted my Freelance Career',
            'description': 'md5:996a28b4f829ed4ffb8302a53d825704',
            'upload_date': '20150818',
            'thumbnail': 're:^https?://.*',
        }
    }]

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')
        url = m.group('mainurl')
        webpage = self._download_webpage(url, video_id)

        media_url_json = self._search_regex(r'"media_url(?:_libsyn)?"\s*:\s*("(\\"|[^"])+")', webpage, 'media_url')
        media_url = self._parse_json(media_url_json, video_id)

        podcast_title = self._html_search_regex( r'<h3\b[^>]*>([^<]+)</h3>', webpage, 'podcast title', default=None)
        episode_title_json = self._search_regex(r'"item_title"\s*:\s*("(\\"|[^"])+")', webpage, 'episode title', default=None)
        episode_title = self._parse_json(episode_title_json, video_id, fatal=False)
        if episode_title is None:
            # Fallback: scrape from page
            episode_title = self._html_search_regex(r'<h4\b[^>]*>([^<]+)', webpage, 'episode title')
        title = '%s - %s' % (podcast_title, episode_title) if podcast_title else episode_title

        description = self._html_search_regex(
            r'<(\w+)\b[^>]*id="info_text_body"[^>]*>(?P<description>.+?)<\/\1>',
            webpage, 'description', default=None, group='description')

        thumbnail_json = self._search_regex(r'"thumbnail_url"\s*:\s*("(\\"|[^"])+")', webpage, 'thumbnail')
        thumbnail = self._parse_json(thumbnail_json, video_id, fatal=False)

        release_date_json = self._search_regex(r'"release_date"\s*:\s*("(\\"|[^"])+")', webpage, 'release date')
        release_date = unified_strdate(self._parse_json(release_date_json, video_id, fatal=False))
        if release_date is None:
            # Fallback: scrape from page
            release_date = unified_strdate(self._search_regex(
                r'<div class="release_date">Released: ([^<]+)<', webpage, 'release date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': release_date,
            'url': media_url,
        }
