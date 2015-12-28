from __future__ import unicode_literals

from .common import InfoExtractor


class ESPNIE(InfoExtractor):
    _VALID_URL = r'https?://espn\.go\.com/(?:[^/]+/)*(?P<id>[^/]+)'
    _WORKING = False
    _TESTS = [{
        'url': 'http://espn.go.com/video/clip?id=10365079',
        'info_dict': {
            'id': 'FkYWtmazr6Ed8xmvILvKLWjd4QvYZpzG',
            'ext': 'mp4',
            'title': 'dm_140128_30for30Shorts___JudgingJewellv2',
            'description': '',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
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
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._search_regex(
            r'class="video-play-button"[^>]+data-id="(\d+)',
            webpage, 'video id')

        player = self._download_webpage(
            'https://espn.go.com/video/iframe/twitter/?id=%s' % video_id, video_id)

        pcode = self._search_regex(
            r'["\']pcode=([^"\']+)["\']', player, 'pcode')

        return self.url_result(
            'ooyalaexternal:espn:%s:%s' % (video_id, pcode),
            'OoyalaExternal')
