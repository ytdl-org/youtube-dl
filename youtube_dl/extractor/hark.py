# -*- coding: utf-8 -*-

import re
import json

from .common import InfoExtractor
from ..utils import determine_ext

class HarkIE(InfoExtractor):
    _VALID_URL = r'https?://www\.hark\.com/clips/(.+?)-.+'
    _TEST = {
        u'url': u'http://www.hark.com/clips/mmbzyhkgny-obama-beyond-the-afghan-theater-we-only-target-al-qaeda-on-may-23-2013',
        u'file': u'mmbzyhkgny.mp3',
        u'md5': u'6783a58491b47b92c7c1af5a77d4cbee',
        u'info_dict': {
            u'title': u"Obama: 'Beyond The Afghan Theater, We Only Target Al Qaeda' on May 23, 2013",
            u'description': u'President Barack Obama addressed the nation live on May 23, 2013 in a speech aimed at addressing counter-terrorism policies including the use of drone strikes, detainees at Guantanamo Bay prison facility, and American citizens who are terrorists.',
            u'duration': 11,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        json_url = "http://www.hark.com/clips/%s.json" %(video_id)
        info_json = self._download_webpage(json_url, video_id)
        info = json.loads(info_json)
        final_url = info['url']

        return {'id': video_id,
                'url' : final_url,
                'title': info['name'],
                'ext': determine_ext(final_url),
                'description': info['description'],
                'thumbnail': info['image_original'],
                'duration': info['duration'],
                }
