# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .common import InfoExtractor


class HarkIE(InfoExtractor):
    _VALID_URL = r'https?://www\.hark\.com/clips/(?P<id>.+?)-.+'
    _TEST = {
        'url': 'http://www.hark.com/clips/mmbzyhkgny-obama-beyond-the-afghan-theater-we-only-target-al-qaeda-on-may-23-2013',
        'md5': '6783a58491b47b92c7c1af5a77d4cbee',
        'info_dict': {
            'id': 'mmbzyhkgny',
            'ext': 'mp3',
            'title': 'Obama: \'Beyond The Afghan Theater, We Only Target Al Qaeda\' on May 23, 2013',
            'description': 'President Barack Obama addressed the nation live on May 23, 2013 in a speech aimed at addressing counter-terrorism policies including the use of drone strikes, detainees at Guantanamo Bay prison facility, and American citizens who are terrorists.',
            'duration': 11,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(
            'http://www.hark.com/clips/%s.json' % video_id, video_id)

        return {
            'id': video_id,
            'url': data['url'],
            'title': data['name'],
            'description': data.get('description'),
            'thumbnail': data.get('image_original'),
            'duration': data.get('duration'),
        }
