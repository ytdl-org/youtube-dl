# -*- coding: utf-8 -*-

import re

from .common import InfoExtractor
from ..utils import determine_ext

class CriterionIE(InfoExtractor):
    _VALID_URL = r'https?://www\.criterion\.com/films/(\d*)-.+'
    _TEST = {
        u'url': u'http://www.criterion.com/films/184-le-samourai',
        u'file': u'184.mp4',
        u'md5': u'bc51beba55685509883a9a7830919ec3',
        u'info_dict': {
            u"title": u"Le Samouraï",
            u"description" : u'md5:a2b4b116326558149bef81f76dcbb93f',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)
        webpage = self._download_webpage(url, video_id)

        final_url = self._search_regex(r'so.addVariable\("videoURL", "(.+?)"\)\;',
                                webpage, 'video url')
        title = self._html_search_regex(r'<meta content="(.+?)" property="og:title" />',
                                webpage, 'video title')
        description = self._html_search_regex(r'<meta name="description" content="(.+?)" />',
                                webpage, 'video description')
        thumbnail = self._search_regex(r'so.addVariable\("thumbnailURL", "(.+?)"\)\;',
                                webpage, 'thumbnail url')

        return {'id': video_id,
                'url' : final_url,
                'title': title,
                'ext': determine_ext(final_url),
                'description': description,
                'thumbnail': thumbnail,
                }
