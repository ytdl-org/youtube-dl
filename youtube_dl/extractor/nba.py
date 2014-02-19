from __future__ import unicode_literals

import re

from .common import InfoExtractor


class NBAIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:watch\.|www\.)?nba\.com/(?:nba/)?video(/[^?]*?)(?:/index\.html)?(?:\?.*)?$'
    _TEST = {
        'url': 'http://www.nba.com/video/games/nets/2012/12/04/0021200253-okc-bkn-recap.nba/index.html',
        'file': u'0021200253-okc-bkn-recap.nba.mp4',
        'md5': u'c0edcfc37607344e2ff8f13c378c88a4',
        'info_dict': {
            'description': 'Kevin Durant scores 32 points and dishes out six assists as the Thunder beat the Nets in Brooklyn.',
            'title': 'Thunder vs. Nets',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        video_url = 'http://ht-mobile.cdn.turner.com/nba/big' + video_id + '_nba_1280x720.mp4'

        shortened_video_id = video_id.rpartition('/')[2]
        title = self._og_search_title(webpage, default=shortened_video_id).replace('NBA.com: ', '')

        description = self._html_search_regex(r'<meta name="description" (?:content|value)="(.*?)" />', webpage, 'description', fatal=False)

        return {
            'id': shortened_video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            'description': description,
        }
