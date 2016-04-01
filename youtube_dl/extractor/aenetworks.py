from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    smuggle_url,
    update_url_query,
    unescapeHTML,
)


class AENetworksIE(InfoExtractor):
    IE_NAME = 'aenetworks'
    IE_DESC = 'A+E Networks: A&E, Lifetime, History.com, FYI Network'
    _VALID_URL = r'https?://(?:www\.)?(?:(?:history|aetv|mylifetime)\.com|fyi\.tv)/(?P<type>[^/]+)/(?:[^/]+/)+(?P<id>[^/]+?)(?:$|[?#])'

    _TESTS = [{
        'url': 'http://www.history.com/topics/valentines-day/history-of-valentines-day/videos/bet-you-didnt-know-valentines-day?m=528e394da93ae&s=undefined&f=1&free=false',
        'info_dict': {
            'id': 'g12m5Gyt3fdR',
            'ext': 'mp4',
            'title': "Bet You Didn't Know: Valentine's Day",
            'description': 'md5:7b57ea4829b391995b405fa60bd7b5f7',
            'timestamp': 1375819729,
            'upload_date': '20130806',
            'uploader': 'AENE-NEW',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
        'add_ie': ['ThePlatform'],
        'expected_warnings': ['JSON-LD'],
    }, {
        'url': 'http://www.history.com/shows/mountain-men/season-1/episode-1',
        'md5': '8ff93eb073449f151d6b90c0ae1ef0c7',
        'info_dict': {
            'id': 'eg47EERs_JsZ',
            'ext': 'mp4',
            'title': 'Winter Is Coming',
            'description': 'md5:641f424b7a19d8e24f26dea22cf59d74',
            'timestamp': 1338306241,
            'upload_date': '20120529',
            'uploader': 'AENE-NEW',
        },
        'add_ie': ['ThePlatform'],
    }, {
        'url': 'http://www.aetv.com/shows/duck-dynasty/video/inlawful-entry',
        'only_matching': True
    }, {
        'url': 'http://www.fyi.tv/shows/tiny-house-nation/videos/207-sq-ft-minnesota-prairie-cottage',
        'only_matching': True
    }, {
        'url': 'http://www.mylifetime.com/shows/project-runway-junior/video/season-1/episode-6/superstar-clients',
        'only_matching': True
    }]

    def _real_extract(self, url):
        page_type, video_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, video_id)

        video_url_re = [
            r'data-href="[^"]*/%s"[^>]+data-release-url="([^"]+)"' % video_id,
            r"media_url\s*=\s*'([^']+)'"
        ]
        video_url = unescapeHTML(self._search_regex(video_url_re, webpage, 'video url'))
        query = {'mbr': 'true'}
        if page_type == 'shows':
            query['assetTypes'] = 'medium_video_s3'
        if 'switch=hds' in video_url:
            query['switch'] = 'hls'

        info = self._search_json_ld(webpage, video_id, fatal=False)
        info.update({
            '_type': 'url_transparent',
            'url': smuggle_url(
                update_url_query(video_url, query),
                {
                    'sig': {
                        'key': 'crazyjava',
                        'secret': 's3cr3t'},
                    'force_smil_url': True
                }),
        })
        return info
