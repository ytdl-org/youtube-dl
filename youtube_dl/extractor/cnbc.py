# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import smuggle_url


class CNBCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www|video)?\.cnbc\.com/(?:gallery|video)/(?:\?video=(?P<id>[0-9]+)|.*/(?P<display_id>[^.]+))'
    _TESTS = [{
        'url': 'http://video.cnbc.com/gallery/?video=3000503714',
        'info_dict': {
            'id': '3000503714',
            'ext': 'mp4',
            'title': 'Fighting zombies is big business',
            'description': 'md5:0c100d8e1a7947bd2feec9a5550e519e',
            'timestamp': 1459332000,
            'upload_date': '20160330',
            'uploader': 'NBCU-CNBC',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'https://www.cnbc.com/video/2018/07/19/trump-i-dont-necessarily-agree-with-raising-rates.html',
        'info_dict': {
            'id': '7000033068',
            'ext': 'mp4',
            'title': 'Full interview with Brian Belski and Tobias Levkovich',
            'description': 'md5:958012776b16f68bad3008587dd0a03a',
            'timestamp': 1532908800,
            'upload_date': '20180730',
            'uploader': 'NBCU-CNBC',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        if not video_id:
            display_id = mobj.group('display_id')
            webpage = self._download_webpage(url, display_id)
            video_id = self._html_search_regex(
                r'<a[^>]+?data-VideoID=[\'"]\s*([0-9]+)\s*',
                webpage, display_id
            )
        return {
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(
                'http://link.theplatform.com/s/gZWlPC/media/guid/2408950221/%s?mbr=true&manifest=m3u' % video_id,
                {'force_smil_url': True}),
            'id': video_id,
        }
