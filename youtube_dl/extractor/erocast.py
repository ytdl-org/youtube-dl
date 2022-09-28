# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ErocastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?erocast\.me/track/(?P<id>[0-9]+)/([a-z]+-)+[a-z]+'
    _TEST = {
        'url': 'https://erocast.me/track/4254/intimate-morning-with-your-wife',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': 4254,
            'ext': 'mp3',
            'mp3': 0,
            'waveform': 0,
            'preview': 0,
            'wav': 0,
            'flac': 0,
            'hd': 0,
            'hls': 1,
            'explicit': 0,
            'selling': 1,
            'price': '0.00',
            'genre': '10,6',
            'mood': None,
            'title': 'Intimate morning  with your wife',
            'description': None,
            'access': None,
            'duration': 1409,
            'artistIds': None,
            'loves': 0,
            'collectors': 0,
            'plays': 2344,
            'released_at': '08/26/2022',
            'copyright': None,
            'allow_download': 0,
            'download_count': 0,
            'allow_comments': 1,
            'comment_count': 0,
            'visibility': 1,
            'approved': 1,
            'pending': 0,
            'created_at': '2022-08-26T19:20:14.000000Z',
            'updated_at': '2022-08-27T11:49:34.000000Z',
            'vocal': 1,
            'script': None,
            'artwork_url': 'https://erocast.me/common/default/song.png',
            'permalink_url': 'https://erocast.me/track/4254/intimate-morning-with-your-wife',
            'stream_url': 'https://erocast.me/stream/hls/4254',
            'favorite': False,
            'library': False,
            'streamable': True,
            'user': {
                'id': 4198,
                'name': 'ZLOY_ASMR',
                'username': 'ZLOY_ASMR',
                'session_id': None,
                'artist_id': 0,
                'collection_count': 0,
                'following_count': 0,
                'follower_count': 0,
                'last_activity': '2022-08-26 19:41:03',
                'notification': None,
                'bio': None,
                'allow_comments': 1,
                'comment_count': 0,
                'script': None,
                'artwork_url': 'https://erocast.me/common/default/user.png',
                'permalink_url': 'https://erocast.me/zloy-asmr'
            },
            'tags': [
                {
                    'id': 48044,
                    'song_id': 4254,
                    'tag': 'morning',
                    'permalink_url': 'https://erocast.me/tracks/tag/morning'
                },
                {
                    'id': 48045,
                    'song_id': 4254,
                    'tag': 'established relationships',
                    'permalink_url': 'https://erocast.me/tracks/tag/established-relationships'
                },
                {
                    'id': 48046,
                    'song_id': 4254,
                    'tag': 'wholesome',
                    'permalink_url': 'https://erocast.me/tracks/tag/wholesome'
                },
                {
                    'id': 48047,
                    'song_id': 4254,
                    'tag': 'kisses',
                    'permalink_url': 'https://erocast.me/tracks/tag/kisses'
                },
                {
                    'id': 48048,
                    'song_id': 4254,
                    'tag': 'wife',
                    'permalink_url': 'https://erocast.me/tracks/tag/wife'
                }
            ]
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
