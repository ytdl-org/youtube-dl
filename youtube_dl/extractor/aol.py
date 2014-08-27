from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .fivemin import FiveMinIE


class AolIE(InfoExtractor):
    IE_NAME = 'on.aol.com'
    _VALID_URL = r'''(?x)
        (?:
            aol-video:|
            http://on\.aol\.com/
            (?:
                video/.*-|
                playlist/(?P<playlist_display_id>[^/?#]+?)-(?P<playlist_id>[0-9]+)[?#].*_videoid=
            )
        )
        (?P<id>[0-9]+)
        (?:$|\?)
    '''

    _TESTS = [{
        'url': 'http://on.aol.com/video/u-s--official-warns-of-largest-ever-irs-phone-scam-518167793?icid=OnHomepageC2Wide_MustSee_Img',
        'md5': '18ef68f48740e86ae94b98da815eec42',
        'info_dict': {
            'id': '518167793',
            'ext': 'mp4',
            'title': 'U.S. Official Warns Of \'Largest Ever\' IRS Phone Scam',
        },
        'add_ie': ['FiveMin'],
    }, {
        'url': 'http://on.aol.com/playlist/brace-yourself---todays-weirdest-news-152147?icid=OnHomepageC4_Omg_Img#_videoid=518184316',
        'info_dict': {
            'id': '152147',
            'title': 'Brace Yourself - Today\'s Weirdest News',
        },
        'playlist_mincount': 10,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        playlist_id = mobj.group('playlist_id')
        if playlist_id and not self._downloader.params.get('noplaylist'):
            self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (playlist_id, video_id))

            webpage = self._download_webpage(url, playlist_id)
            title = self._html_search_regex(
                r'<h1 class="video-title[^"]*">(.+?)</h1>', webpage, 'title')
            playlist_html = self._search_regex(
                r"(?s)<ul\s+class='video-related[^']*'>(.*?)</ul>", webpage,
                'playlist HTML')
            entries = [{
                '_type': 'url',
                'url': 'aol-video:%s' % m.group('id'),
                'ie_key': 'Aol',
            } for m in re.finditer(
                r"<a\s+href='.*videoid=(?P<id>[0-9]+)'\s+class='video-thumb'>",
                playlist_html)]

            return {
                '_type': 'playlist',
                'id': playlist_id,
                'display_id': mobj.group('playlist_display_id'),
                'title': title,
                'entries': entries,
            }

        return FiveMinIE._build_result(video_id)
