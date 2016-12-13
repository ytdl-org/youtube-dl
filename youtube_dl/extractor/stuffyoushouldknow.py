# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor

import re


class StuffyoushouldknowIE(InfoExtractor):
    _VALID_URL = r'https?://?(www).stuffyoushouldknow.com/podcasts/(?P<id>[[a-zA-Z0-9_-]+)'
    _TEST = {
        'url': 'http://www.stuffyoushouldknow.com/podcasts/banned-kids-advertising.htm',
        'md5': '12cfeb58e11776addb58ce37c12711b7',
        'info_dict': {
            'title': 'Should Advertising to Kids Be Banned?',
            'url': 'http://www.stuffyoushouldknow.com/podcasts/banned-kids-advertising.htm',
            'site_name': 'Stuff You Should Know',
            'description': 'As kids’ buying power in America has exploded in recent decades, so too has the amount companies spend advertising to them. But because of a quirk of brain development, kids aren’t equipped to understand ads are manipulating them. Should they be banned?',
            'content': 'http://s.hswstatic.com/gif/banned-kids-advertising-sysk.jpg',
        },

    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id=mobj.group('id')
        webpage = self._download_webpage(url, video_id)

        video_url = re.search(r'https?://www.podtrac.com/pts/redirect.mp3/podcasts.howstuffworks.com/hsw/podcasts'
                              r'/sysk/[0-9a-zA-Z_-]*.mp3', webpage)
        title = self._og_search_title(webpage)
        site_name= self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'site name': site_name,
            'url': video_url.group(0)
        }