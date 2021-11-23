# coding: utf-8
from __future__ import unicode_literals
import re
from datetime import datetime
from ..utils import float_or_none, try_get, str_to_int, unified_timestamp
from ..compat import compat_str
from .common import InfoExtractor


class PodchaserIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?podchaser\.com/
        (?:(?:podcasts)|(?:creators))
        /[\w-]+-
        (?:
            (?P<creator_id>[\d]+[\w]+)|(?P<podcast_id>[\d]+))
        (?:/episodes/[\w\-]+-
            (?P<id>[\d]+))?'''

    _TESTS = [{
        'url': 'https://www.podchaser.com/podcasts/cum-town-36924/episodes/ep-285-freeze-me-off-104365585',
        'info_dict': {
            'id': '104365585',
            'title': "Ep. 285 – freeze me off",
            'description': 'cam ahn',
            'thumbnail': r're:^https?://.*\.jpg$',
            'ext': 'mp3',
            'categories': ['Comedy'],
            'series': 'Cum Town',
            'duration': 3708,
            'timestamp': 1636531259,
            'upload_date': '20211110'
        }
    }, {
        'url': 'https://www.podchaser.com/podcasts/the-bone-zone-28853',
        'info_dict': {
            'id': '28853',
            'title': 'The Bone Zone',
            'description': 'md5:c39acd897170a8bf3ad94fc45dc25060',
        },
        'playlist_count': 6
    }, {
        'url': 'https://www.podchaser.com/creators/todd-glass-107ZzkFiEQ',
        'info_dict': {
            'id': '107ZzkFiEQ',
            'title': 'Todd Glass',
            'description': 'md5:0771e81d879f304f11254e5a56a97a58',
        },
        'playlist_mincount': 48
    }, {
        'url': 'https://www.podchaser.com/podcasts/sean-carrolls-mindscape-scienc-699349/episodes',
        'info_dict': {
            'id': '699349',
            'title': "Sean Carroll's Mindscape: Science, Society, Philosophy, Culture, Arts, and Ideas",
            'description': 'md5:8692ce0c50cb900c5e4eb27b437dd67b'
        },
        'playlist_count': 25
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        audio_id, podcast_id, creator_id = mobj.group('id'), \
            mobj.group('podcast_id'), mobj.group('creator_id')
        webpage = self._download_webpage(url, audio_id)
        page_title = self._html_search_meta(['title', 'og:title', 'twitter:title'], webpage, default=None) \
            or self._search_regex(
                r'<h1[^>]*>(.+?)</h1>', webpage, 'title', fatal=False, default="Podchaser Podcast")
        page_description = self._html_search_meta(['description', 'og:description', 'twitter:description'], webpage, default=None)

        data = self._search_regex(
            r'window.__APP_STATE__\s*=\s*(["\']?{.+?}["\']?);</script>', webpage, 'app state')

        while isinstance(data, compat_str):
            data = self._parse_json(data, audio_id)

        episodes = try_get(data, lambda x: x['podcast']['episodes']['entities'], dict) or {}
        episode_list = [(episodes.get(episode_id), episode_id) for episode_id in episodes]

        entries = [{
            'id': episode_id,
            'title': episode.get('title'),
            'description': episode.get('description'),
            'url': episode.get('audio_url'),
            'thumbnail': try_get(episode, lambda x: x['podcast']['image_url']),
            'duration': str_to_int(episode.get('length')),
            'timestamp': unified_timestamp(episode.get('air_date')),
            'rating': float_or_none(episode.get('rating')),
            'categories': [x['text'] for x in try_get(episode, lambda x: x['podcast']['categories'], list) or []],
            'tags': [tag['text'] for tag in episode.get('tags') or []],
            'series': try_get(episode, lambda x: x['podcast']['title'], compat_str),
        } for episode, episode_id in episode_list]

        if len(entries) > 1:
            return self.playlist_result(
                entries, playlist_id=(creator_id or podcast_id), playlist_title=page_title,
                playlist_description=page_description)

        return entries[0]
