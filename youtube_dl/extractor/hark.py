# -*- coding: utf-8 -*-

import re

from .common import InfoExtractor
from ..utils import determine_ext

class HarkIE(InfoExtractor):
    _VALID_URL = r'https?://www\.hark\.com/clips/(.+?)-.+'
    _TEST = {
        u'url': u'http://www.hark.com/clips/mmbzyhkgny-obama-beyond-the-afghan-theater-we-only-target-al-qaeda-on-may-23-2013',
        u'file': u'mmbzyhkgny.mp3',
        u'md5': u'6783a58491b47b92c7c1af5a77d4cbee',
        u'info_dict': {
            u"title": u"Obama: 'Beyond The Afghan Theater, We Only Target Al Qaeda' On May 23, 2013 ",
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        embed_url = "http://www.hark.com/clips/%s/homepage_embed" %(video_id)
        webpage = self._download_webpage(embed_url, video_id)

        final_url = self._search_regex(r'src="(.+?).mp3"',
                                webpage, 'video url')+'.mp3'
        title = self._html_search_regex(r'<title>(.+?)</title>',
                                webpage, 'video title').replace(' Sound Clip and Quote - Hark','').replace(
                                'Sound Clip , Quote, MP3, and Ringtone - Hark','')

        return {'id': video_id,
                'url' : final_url,
                'title': title,
                'ext': determine_ext(final_url),
                }
