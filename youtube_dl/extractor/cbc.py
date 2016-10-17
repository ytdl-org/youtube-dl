# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import js_to_json


class CBCIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cbc\.ca/(?:[^/]+/)+(?P<id>[^/?#]+)'
    _TESTS = [{
        # with mediaId
        'url': 'http://www.cbc.ca/22minutes/videos/clips-season-23/don-cherry-play-offs',
        'info_dict': {
            'id': '2682904050',
            'ext': 'flv',
            'title': 'Don Cherry – All-Stars',
            'description': 'Don Cherry has a bee in his bonnet about AHL player John Scott because that guy’s got heart.',
            'timestamp': 1454475540,
            'upload_date': '20160203',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # with clipId
        'url': 'http://www.cbc.ca/archives/entry/1978-robin-williams-freestyles-on-90-minutes-live',
        'info_dict': {
            'id': '2487345465',
            'ext': 'flv',
            'title': 'Robin Williams freestyles on 90 Minutes Live',
            'description': 'Wacky American comedian Robin Williams shows off his infamous "freestyle" comedic talents while being interviewed on CBC\'s 90 Minutes Live.',
            'upload_date': '19700101',
            'uploader': 'CBCC-NEW',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }, {
        # multiple iframes
        'url': 'http://www.cbc.ca/natureofthings/blog/birds-eye-view-from-vancouvers-burrard-street-bridge-how-we-got-the-shot',
        'playlist': [{
            'info_dict': {
                'id': '2680832926',
                'ext': 'flv',
                'title': 'An Eagle\'s-Eye View Off Burrard Bridge',
                'description': 'Hercules the eagle flies from Vancouver\'s Burrard Bridge down to a nearby park with a mini-camera strapped to his back.',
                'upload_date': '19700101',
            },
        }, {
            'info_dict': {
                'id': '2658915080',
                'ext': 'flv',
                'title': 'Fly like an eagle!',
                'description': 'Eagle equipped with a mini camera flies from the world\'s tallest tower',
                'upload_date': '19700101',
            },
        }],
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }]

    @classmethod
    def suitable(cls, url):
        return False if CBCPlayerIE.suitable(url) else super(CBCIE, cls).suitable(url)

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        player_init = self._search_regex(
            r'CBC\.APP\.Caffeine\.initInstance\(({.+?})\);', webpage, 'player init',
            default=None)
        if player_init:
            player_info = self._parse_json(player_init, display_id, js_to_json)
            media_id = player_info.get('mediaId')
            if not media_id:
                clip_id = player_info['clipId']
                media_id = self._download_json(
                    'http://feed.theplatform.com/f/h9dtGB/punlNGjMlc1F?fields=id&byContent=byReleases%3DbyId%253D' + clip_id,
                    clip_id)['entries'][0]['id'].split('/')[-1]
            return self.url_result('cbcplayer:%s' % media_id, 'CBCPlayer', media_id)
        else:
            entries = [self.url_result('cbcplayer:%s' % media_id, 'CBCPlayer', media_id) for media_id in re.findall(r'<iframe[^>]+src="[^"]+?mediaId=(\d+)"', webpage)]
            return self.playlist_result(entries)


class CBCPlayerIE(InfoExtractor):
    _VALID_URL = r'(?:cbcplayer:|https?://(?:www\.)?cbc\.ca/(?:player/play/|i/caffeine/syndicate/\?mediaId=))(?P<id>\d+)'
    _TEST = {
        'url': 'http://www.cbc.ca/player/play/2683190193',
        'info_dict': {
            'id': '2683190193',
            'ext': 'flv',
            'title': 'Gerry Runs a Sweat Shop',
            'description': 'md5:b457e1c01e8ff408d9d801c1c2cd29b0',
            'timestamp': 1455067800,
            'upload_date': '20160210',
        },
        'params': {
            # rtmp download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        return self.url_result(
            'http://feed.theplatform.com/f/ExhSPC/vms_5akSXx4Ng_Zn?byGuid=%s' % video_id,
            'ThePlatformFeed', video_id)
