# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class BelgianNationalIE(InfoExtractor):    
    _VALID_URL = r'http://(?:deredactie|sporza|cobra)\.be/cm/(.*)/(?P<video_id>[^\']+)'
    _TESTS = [
    # deredactie.be
    {
        'url': 'http://deredactie.be/cm/vrtnieuws/videozone/programmas/journaal/EP_141025_JOL',
        'md5': '4cebde1eb60a53782d4f3992cbd46ec8',
        'info_dict': {
            'id': 'EP_141025_JOL',
            'title': 'Het journaal L - 25/10/14',
            'ext': 'mp4',
            'duration': 929,
        }
    },
    # sporza.be
    {
        'url': 'http://sporza.be/cm/sporza/videozone/programmas/extratime/EP_141020_Extra_time',
        'md5': '11f53088da9bf8e7cfc42456697953ff',
        'info_dict': {
            'id': 'EP_141020_Extra_time',
            'title': 'Bekijk Extra Time van 20 oktober',
            'ext': 'mp4',
            'duration': 3238,
        }
        
    },
    # cobra.be
    {
        'url': 'http://cobra.be/cm/cobra/videozone/rubriek/film-videozone/141022-mv-ellis-cafecorsari',
        'md5': '78a2b060a5083c4f055449a72477409d',
        'info_dict': {
            'id': '141022-mv-ellis-cafecorsari',
            'title': 'Bret Easton Ellis in Café Corsari',
            'ext': 'mp4',
            'duration': 661,
        }
    }
    ]
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('video_id')
        
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage)
        
        video_url = self._search_regex(r'data-video-src="(.*?)"', webpage, 'Video url') + '/manifest.f4m'
        duration = int_or_none(self._search_regex(r'data-video-sitestat-duration="(.*?)"', webpage, 'Duration'))
        
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'duration': duration,
        }