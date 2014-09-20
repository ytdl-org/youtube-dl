# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import url_basename


class BehindKinkIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?behindkink\.com/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/(?P<id>[^/#?_]+)'
    _TEST = {
        'url': 'http://www.behindkink.com/2014/08/14/ab1576-performers-voice-finally-heard-the-bill-is-killed/',
        'md5': '41ad01222b8442089a55528fec43ec01',
        'info_dict': {
            'id': '36370',
            'ext': 'mp4',
            'title': 'AB1576 - PERFORMERS VOICE FINALLY HEARD - THE BILL IS KILLED!',
            'description': 'The adult industry voice was finally heard as Assembly Bill 1576 remained\xa0 in suspense today at the Senate Appropriations Hearing. AB1576 was, among other industry damaging issues, a condom mandate...',
            'upload_date': '20140814',
            'thumbnail': 'http://www.behindkink.com/wp-content/uploads/2014/08/36370_AB1576_Win.jpg',
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
            r"'file':\s*'([^']+)'",
            webpage, 'URL base')

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
