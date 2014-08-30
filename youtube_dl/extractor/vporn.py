# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import int_or_none

class VpornIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?vporn\.com/[a-z]+/(?P<title_dash>[a-z-]+)/(?P<id>\d+)/?'
    _TEST = {
        'url': 'http://www.vporn.com/masturbation/violet-on-her-th-birthday/497944/',
        'md5': 'facf37c1b86546fa0208058546842c55',
        'info_dict': {
            'id': '497944',
            'ext': 'mp4',
            'title': 'Violet On Her 19th Birthday',
            'description': 'Violet dances in front of the camera which is sure to get you horny.',
            'duration': 393,
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.*?) - Vporn Video</title>', webpage, 'title')
        video_url = self._html_search_regex(r'flashvars.videoUrlMedium  = "(.*?)"', webpage, 'video_url')
        description = self._html_search_regex(r'<div class="description_txt">(.*?)</div>', webpage, 'description')
        thumbnail = 'http://www.vporn.com' + self._html_search_regex(r'flashvars.imageUrl = "(.*?)"', webpage, 'description')

        mobj = re.search(r'<span class="f_right">duration (?P<minutes>\d+) min (?P<seconds>\d+) sec </span>', webpage)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        mobj = re.search(r'<span>((?P<thousands>\d+),)?(?P<units>\d+) VIEWS</span>', webpage)
        view_count = int(mobj.group('thousands')) * 1000 + int(mobj.group('units')) if mobj else None

        return {
            'id': video_id,
            'url': video_url,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': int_or_none(duration),
            'view_count': int_or_none(view_count),
        }
