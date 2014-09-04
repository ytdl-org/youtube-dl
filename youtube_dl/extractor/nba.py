from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    remove_end,
    parse_duration,
)


class NBAIE(InfoExtractor):
    _VALID_URL = r'https?://(?:watch\.|www\.)?nba\.com/(?:nba/)?video(?P<id>/[^?]*?)(?:/index\.html)?(?:\?.*)?$'
    _TEST = {
        'url': 'http://www.nba.com/video/games/nets/2012/12/04/0021200253-okc-bkn-recap.nba/index.html',
        'md5': 'c0edcfc37607344e2ff8f13c378c88a4',
        'info_dict': {
            'id': '0021200253-okc-bkn-recap.nba',
            'ext': 'mp4',
            'title': 'Thunder vs. Nets',
            'description': 'Kevin Durant scores 32 points and dishes out six assists as the Thunder beat the Nets in Brooklyn.',
            'duration': 181,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        video_url = 'http://ht-mobile.cdn.turner.com/nba/big' + video_id + '_nba_1280x720.mp4'

        shortened_video_id = video_id.rpartition('/')[2]
        title = remove_end(
            self._og_search_title(webpage, default=shortened_video_id), ' : NBA.com')

        description = self._og_search_description(webpage)
        duration = parse_duration(
            self._html_search_meta('duration', webpage, 'duration', fatal=False))


        return {
            'id': shortened_video_id,
            'url': video_url,
            'title': title,
            'description': description,
            'duration': duration,
        }
