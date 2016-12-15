# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor

import re


class StuffyoushouldknowIE(InfoExtractor):
    _VALID_URL = r'https?://?(www).stuffyoushouldknow.com/podcasts/(?P<id>[[a-zA-Z0-9_-]+)'
    _TEST = {
        'url': 'http://www.stuffyoushouldknow.com/podcasts/banned-kids-advertising.htm',
        'md5': 'e128341f40a8be82ac8f55cb0e402d7d',
        'info_dict': {
            'id':'banned-kids-advertising',
            'ext':'mp3',
            'title': 'Should Advertising to Kids Be Banned?',
            'description': 'As kids’ buying power in America has exploded in recent decades, so too has the amount companies spend advertising to them. But because of a quirk of brain development, kids aren’t equipped to understand ads are manipulating them. Should they be banned?',
        },

    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id=mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = re.search(r'https?://www.podtrac.com/pts/redirect.mp3/podcasts.howstuffworks.com/hsw/podcasts'
                              r'/sysk/[0-9a-zA-Z_-]*.mp3', webpage)
        site_name= self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': video_id,
            'title': site_name,
            'description': description,
            'url': video_url.group(0),
            'ext': 'mp3',
            'site_name': site_name,

        }