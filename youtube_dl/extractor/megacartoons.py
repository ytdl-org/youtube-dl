# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor


class MegaCartoonsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?megacartoons\.net/(?P<id>[a-z-]+)/'
    _TEST = {
        'url': 'https://www.megacartoons.net/help-wanted/',
        'md5': '4ba9be574f9a17abe0c074e2f955fded',
        'info_dict': {
            'id': 'help-wanted',
            'title': 'Help Wanted',
            'ext': 'mp4',
            'thumbnail': r're:^https?://.*\.jpg$',
            'description': 'Help Wanted: Encouraged by his best friend, Patrick Starfish, '
                           'SpongeBob overcomes his fears and finally applies for that '
                           'dream job as a fry cook at the Krusty Krab. Challenged by the '
                           'owner, Mr. Krabs, and his assistant Squidward, to prove himself '
                           'worthy of the job, SpongeBob rises to the occasion, with the help '
                           'of one very special spatula, by feeding a sea of ravenous anchovies.'
        }
    }

    def _real_extract(self, url):
        # ID is equal to the episode name
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Try to find a good title or fallback to the ID
        title = self._og_search_title(webpage) or video_id

        # Video data is stored in a json -> extract it from the raw html
        url_json = json.loads(self._html_search_regex(r'<div.*data-item=["/\'](?P<videourls>{.*})["/\'].*>', webpage, 'videourls'))

        video_url = url_json.get('sources')[0].get('src') or self._og_search_video_url(webpage)    # Get the video url
        video_type = url_json.get('sources')[0].get('type')                                        # Get the video type -> 'video/mp4'
        video_thumbnail = url_json.get('splash') or self._og_search_thumbnail(webpage)             # Get the thumbnail

        # Every video has a short summary -> save it as description
        video_description = self._html_search_regex(r'<p>(?P<videodescription>.*)</p>', webpage, 'videodescription', fatal=False) or self._og_search_description(webpage)

        return {
            'id': video_id,
            'title': title,
            'format': video_type,
            'url': video_url,
            'thumbnail': video_thumbnail,
            'description': video_description,
        }
