# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from urllib import parse

class ESPNFCIE(InfoExtractor):
    _VALID_URL = r'http?:\/\/(?:www\.)?espnfc\.us\/video\/((?:[a-z][a-z0-9_-]*))\/((?:[0-9]*))/video/(?P<id>[^/]+)/((?:[a-z][a-z0-9_-]*))'
    _TESTS = [
                {
                'url': 'http://www.espnfc.us/video/mls-highlights/150/video/2743663/must-see-moments-best-of-the-mls-season',
                'info_dict': {
                    'id': '2743663',
                    'ext': 'mp4',
                    'title': 'Must-See Moments: Best of the MLS season',
                    'description': 'Relive the best moments of the 2015 MLS season, including the arrival of new stars and the crowning of a first-time champion.</p>',
                    'thumbnail': 'http://a.espncdn.com/combiner/i/?img=/media/motion/2015/1207/int_151206_Must_See_Moments_Best_of_MLS_2015_seaso145/int_151206_Must_See_Moments_Best_of_MLS_2015_seaso145.jpg&w=1500&h=1500&scale=crop&site=espnfc',
                    }
                },
                {
                    'url': 'http://www.espnfc.us/video/espn-fc-tv/86/video/2774391/drogba-set-to-quit-montreal-for-chelsea',
                    'info_dict': {
                        'id': '2774391',
                        'ext': 'mp4',
                        'title': 'Drogba set to quit Montreal for Chelsea?',
                        'description': 'The ESPN FC team discuss reports that ex-Chelsea forward Didier Drogba is considering leaving Montreal to coach at Chelsea.</p>',
                        'thumbnail': 'http://a.espncdn.com/combiner/i/?img=/media/motion/ESPNi/2015/1229/int_151229_INET_FC_DROGBA_TO_CHELSEA/int_151229_INET_FC_DROGBA_TO_CHELSEA.jpg&w=1500&h=1500&scale=crop&site=espnfc',
                    }
                }
        ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        twitter_player_stream = self._html_search_meta('twitter:player:stream', webpage)

        # Obtain reference to Once URL using an index on the Twitter player stream, add four to start at
        onceurl_start = twitter_player_stream.index('url=') + 4

        video_url = parse.unquote(twitter_player_stream[onceurl_start:]).replace('.once', '.mp4')

        formats = [{
             'url': video_url,
        }]

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
        }
