# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class EpornerIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?eporner\.com/hd-porn/(?P<id>\d+)/(?P<title_dash>[\w-]+)/?'
    _TEST = {
        'url': 'http://www.eporner.com/hd-porn/95008/Infamous-Tiffany-Teen-Strip-Tease-Video/',
        'md5': '3b427ae4b9d60619106de3185c2987cd',
        'info_dict': {
            'id': '95008',
            'ext': 'flv',
            'title': 'Infamous Tiffany Teen Strip Tease Video',
            'duration': 194
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.*?) - EPORNER', webpage, 'title')

        redirect_code = self._html_search_regex(r'<script type="text/javascript" src="/config5/'+str(video_id)+'/([a-f\d]+)/">', webpage, 'redirect_code')
        redirect_url = 'http://www.eporner.com/config5/' + str(video_id) +'/'+ redirect_code
        webpage2 = self._download_webpage(redirect_url, video_id)
        video_url = self._html_search_regex(r'file: "(.*?)",', webpage2, 'video_url')

        mobj = re.search(r'class="mbtim">(?P<minutes>\d+):(?P<seconds>\d+)</div>', webpage)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        mobj = re.search(r'id="cinemaviews">((?P<thousands>\d+),)?(?P<units>\d+)<small>views', webpage)
        view_count = int(mobj.group('thousands')) * 1000 + int(mobj.group('units')) if mobj else None

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'duration': int_or_none(duration),
            'view_count': int_or_none(view_count),
        }
