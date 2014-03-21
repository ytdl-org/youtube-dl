from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .fivemin import FiveMinIE


class AolIE(InfoExtractor):
    IE_NAME = 'on.aol.com'
    _VALID_URL = r'http://on\.aol\.com/video/.*-(?P<id>\d+)($|\?)'

    _TEST = {
        'url': 'http://on.aol.com/video/u-s--official-warns-of-largest-ever-irs-phone-scam-518167793?icid=OnHomepageC2Wide_MustSee_Img',
        'md5': '18ef68f48740e86ae94b98da815eec42',
        'info_dict': {
            'id': '518167793',
            'ext': 'mp4',
            'title': 'U.S. Official Warns Of \'Largest Ever\' IRS Phone Scam',
        },
        'add_ie': ['FiveMin'],
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        self.to_screen('Downloading 5min.com video %s' % video_id)
        return FiveMinIE._build_result(video_id)
