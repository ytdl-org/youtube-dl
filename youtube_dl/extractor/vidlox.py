# coding: utf-8
from __future__ import unicode_literals

import re

from ..utils   import ExtractorError
from .common   import InfoExtractor
from .openload import PhantomJSwrapper


class VidloxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vidlox\.(?:me|tv)/(?:embed-)?(?P<id>[0-9a-z]+)(?:\.html)?'

    _TESTS = [{
        'url': 'https://vidlox.me/5tq733o3wj1d',
        'md5': 'f780592146ad0458679064de891f3e3f',
        'info_dict': {
            'id': '5tq733o3wj1d',
            'ext': 'mp4',
            'title': r're:big buck bunny 1080p surround',
            'thumbnail': r're:^https?://.*\.jpg$',
            'subtitles': {
                'Spanish': [{
                    'ext': 'srt',
                }],
            }
        }
    }, {
        'url': 'https://vidlox.me/embed-bs2nk6dgqio1.html',
        'only_matching': True,
    }]
    


    def _real_extract(self, url):

        video_id = self._match_id(url)
        page_url = "https://vidlox.me/%s" % video_id
        phantom = PhantomJSwrapper(self, required_version='2.0')

        # download page for couple simple test
        webpage = self._download_webpage(page_url, video_id).replace("\n","").replace("\t","")
        if 'File not found' in webpage:
            raise ExtractorError('File not found', expected=True, video_id=video_id)

        title = None
        if 'This video can be watched as embed only.' in webpage:
            # extract tilte and download embed
            title = self._html_search_regex(
                r'<title[^>]*?>(?P<title>.+?)\s*</title>', webpage, 'title').replace('Watch ','',1)
            webpage = None
            page_url = "https://vidlox.me/embed-%s.html" % video_id

        # execute JS
        webpage, _ = phantom.get(page_url, webpage, video_id=video_id)



        # extract player data
        clappr_dict = self._find_clappr_data(webpage, video_id)
        if not clappr_dict:
            raise ExtractorError('Player data not found', 
                                expected=False, video_id=video_id)

        # and parse it
        info_dict = self._parse_clappr_data(clappr_dict, 
                            video_id=video_id, base_url=page_url)

        info_dict['title'] = title or self._html_search_regex(
                r'<h1[^>]*?>(?P<title>.+?)\s*</h1>', webpage, 'title')

        


        return info_dict
