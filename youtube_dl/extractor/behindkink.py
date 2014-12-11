# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import url_basename


class BehindKinkIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?behindkink\.com/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<id>[^/#?_]+)'
    _TEST = {
        'url': 'http://www.behindkink.com/2014/12/05/what-are-you-passionate-about-marley-blaze/',
        'md5': '507b57d8fdcd75a41a9a7bdb7989c762',
        'info_dict': {
            'id': '37127',
            'ext': 'mp4',
            'title': 'What are you passionate about – Marley Blaze',
            'description': 'Getting a better understanding of the talent that comes through the doors of the Armory is one of our missions at Behind Kink. Asking the question what are you passionate about helps us get a littl...',
            'upload_date': '20141205',
            'thumbnail': 'http://www.behindkink.com/wp-content/uploads/2014/12/blaze-1.jpg',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')
        year = mobj.group('year')
        month = mobj.group('month')
        day = mobj.group('day')
        upload_date = year + month + day

        webpage = self._download_webpage(url, display_id)

        video_url = self._search_regex(
            r'<source src="(.*?)" type="video/mp4" />', webpage, 'video URL')

        video_id = url_basename(video_url)
        video_id = video_id.split('_')[0]

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': self._og_search_title(webpage),
            'display_id': display_id,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage),
            'upload_date': upload_date,
            'age_limit': 18,
        }
