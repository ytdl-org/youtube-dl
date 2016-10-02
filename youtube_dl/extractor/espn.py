from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import remove_end


class ESPNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:espn\.go|(?:www\.)?espn)\.com/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://espn.go.com/video/clip?id=10365079',
        'md5': '60e5d097a523e767d06479335d1bdc58',
        'info_dict': {
            'id': 'FkYWtmazr6Ed8xmvILvKLWjd4QvYZpzG',
            'ext': 'mp4',
            'title': '30 for 30 Shorts: Judging Jewell',
            'description': None,
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['OoyalaExternal'],
    }, {
        # intl video, from http://www.espnfc.us/video/mls-highlights/150/video/2743663/must-see-moments-best-of-the-mls-season
        'url': 'http://espn.go.com/video/clip?id=2743663',
        'md5': 'f4ac89b59afc7e2d7dbb049523df6768',
        'info_dict': {
            'id': '50NDFkeTqRHB0nXBOK-RGdSG5YQPuxHg',
            'ext': 'mp4',
            'title': 'Must-See Moments: Best of the MLS season',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['OoyalaExternal'],
    }, {
        'url': 'https://espn.go.com/video/iframe/twitter/?cms=espn&id=10365079',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/recap?gameId=400793786',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/blog/golden-state-warriors/post/_/id/593/how-warriors-rapidly-regained-a-winning-edge',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/sports/endurance/story/_/id/12893522/dzhokhar-tsarnaev-sentenced-role-boston-marathon-bombings',
        'only_matching': True,
    }, {
        'url': 'http://espn.go.com/nba/playoffs/2015/story/_/id/12887571/john-wall-washington-wizards-no-swelling-left-hand-wrist-game-5-return',
        'only_matching': True,
    }, {
        'url': 'http://www.espn.com/video/clip?id=10365079',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'class=(["\']).*?video-play-button.*?\1[^>]+data-id=["\'](?P<id>\d+)',
            webpage, 'video id', group='id')

        cms = 'espn'
        if 'data-source="intl"' in webpage:
            cms = 'intl'
        player_url = 'https://espn.go.com/video/iframe/twitter/?id=%s&cms=%s' % (video_id, cms)
        player = self._download_webpage(
            player_url, video_id)

        pcode = self._search_regex(
            r'["\']pcode=([^"\']+)["\']', player, 'pcode')

        title = remove_end(
            self._og_search_title(webpage),
            '- ESPN Video').strip()

        return {
            '_type': 'url_transparent',
            'url': 'ooyalaexternal:%s:%s:%s' % (cms, video_id, pcode),
            'ie_key': 'OoyalaExternal',
            'title': title,
        }
