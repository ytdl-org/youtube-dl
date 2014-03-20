from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    US_RATINGS,
)


class PBSIE(InfoExtractor):
    _VALID_URL = r'''(?x)https?://
        (?:
            # Direct video URL
            video\.pbs\.org/(?:viralplayer|video)/(?P<id>[0-9]+)/? |
            # Article with embedded player
           (?:www\.)?pbs\.org/(?:[^/]+/){2,5}(?P<presumptive_id>[^/]+)/?(?:$|[?\#]) |
           # Player
           video\.pbs\.org/(?:widget/)?partnerplayer/(?P<player_id>[^/]+)/
        )
    '''

    _TEST = {
        'url': 'http://www.pbs.org/tpt/constitution-usa-peter-sagal/watch/a-more-perfect-union/',
        'md5': 'ce1888486f0908d555a8093cac9a7362',
        'info_dict': {
            'id': '2365006249',
            'ext': 'mp4',
            'title': 'A More Perfect Union',
            'description': 'md5:ba0c207295339c8d6eced00b7c363c6a',
            'duration': 3190,
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        presumptive_id = mobj.group('presumptive_id')
        display_id = presumptive_id
        if presumptive_id:
            webpage = self._download_webpage(url, display_id)
            url = self._search_regex(
                r'<iframe\s+id=["\']partnerPlayer["\'].*?\s+src=["\'](.*?)["\']>',
                webpage, 'player URL')
            mobj = re.match(self._VALID_URL, url)

        player_id = mobj.group('player_id')
        if not display_id:
            display_id = player_id
        if player_id:
            player_page = self._download_webpage(
                url, display_id, note='Downloading player page',
                errnote='Could not download player page')
            video_id = self._search_regex(
                r'<div\s+id="video_([0-9]+)"', player_page, 'video ID')
        else:
            video_id = mobj.group('id')
            display_id = video_id

        info_url = 'http://video.pbs.org/videoInfo/%s?format=json' % video_id
        info = self._download_json(info_url, display_id)

        rating_str = info.get('rating')
        if rating_str is not None:
            rating_str = rating_str.rpartition('-')[2]
        age_limit = US_RATINGS.get(rating_str)

        return {
            'id': video_id,
            'title': info['title'],
            'url': info['alternate_encoding']['url'],
            'ext': 'mp4',
            'description': info['program'].get('description'),
            'thumbnail': info.get('image_url'),
            'duration': info.get('duration'),
            'age_limit': age_limit,
        }
