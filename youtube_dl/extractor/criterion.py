# -*- coding: utf-8 -*-

import re

from .common import InfoExtractor

class CriterionIE(InfoExtractor):
    _VALID_URL = r'http://www.criterion.com/films/(.*)'
    _TEST = {
        u'url': u'http://www.criterion.com/films/184-le-samourai',
        u'file': u'184.mp4',
        u'md5': u'bc51beba55685509883a9a7830919ec3',
        u'info_dict': {
            u"title": u"Le Samouraï",
            u"description" : u"In a career-defining performance, Alain Delon plays a contract killer with samurai instincts. A razor-sharp cocktail of 1940s American gangster cinema and 1960s French pop culture, maverick director Jean-Pierre Melville&#x27;s masterpiece _Le Samouraï_ defines cool. "
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1).split('-')[0]
        webpage = self._download_webpage(url, video_id)

        final_url = self._search_regex(r'so.addVariable\("videoURL", "(.+?)"\)\;',
                                webpage, 'video url')
        title = self._search_regex(r'<meta content="(.+?)" property="og:title" />',
                                webpage, 'video title')
        description = self._search_regex(r'<meta name="description" content="(.+?)" />',
                                webpage, 'video description')
        thumbnail = self._search_regex(r'so.addVariable\("thumbnailURL", "(.+?)"\)\;',
                                webpage, 'thumbnail url')
        ext = final_url.split('.')[-1]

        return {'id': video_id,
                'url' : final_url,
                'title': title,
                'ext': ext,
                'description': description,
                'thumbnail': thumbnail,
                }
