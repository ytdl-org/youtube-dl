from __future__ import unicode_literals

import re

from .common import InfoExtractor

class News18IE(InfoExtractor):
    _VALID_URL = r'''https?:\/\/www\.news18\.com[a-zA-Z0-9_\/-]+-(?P<id>\d+)\.html'''
    _TEST = {
        'url' : 'https://www.news18.com/news/ivideos/inside-naxal-bastion-news18-visits-the-villages-voting-first-time-ever-1928149.html',
        'md5' : 'cb5a78310f3e583da5ba0de38b450938',
        'info_dict': {
            'id': '1928149',
            'ext': 'mp4',
            'title': 'Inside Naxal Bastion: News18 Visits The Villages Voting First Time Ever',
        }
    }

    def _real_extract(self, url):
        IE_NAME = 'News18'
        video_id = self._match_id(url)
        webpage = self._download_webpage(url,video_id)
        video_url = self._search_regex(r'(?P<url>https?:\/\/vodpd\.news18\.com[\/\w_-]+\.mp4)', webpage, 'video URL',default='')
        title = self._og_search_title(webpage)

        print(video_url)
        print(video_id)
        print(title)
        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'ext': 'mp4'
        }

