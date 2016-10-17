# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class BuzzFeedIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?buzzfeed\.com/[^?#]*?/(?P<id>[^?#]+)'
    _TESTS = [{
        'url': 'http://www.buzzfeed.com/abagg/this-angry-ram-destroys-a-punching-bag-like-a-boss?utm_term=4ldqpia',
        'info_dict': {
            'id': 'this-angry-ram-destroys-a-punching-bag-like-a-boss',
            'title': 'This Angry Ram Destroys A Punching Bag Like A Boss',
            'description': 'Rambro!',
        },
        'playlist': [{
            'info_dict': {
                'id': 'aVCR29aE_OQ',
                'ext': 'mp4',
                'upload_date': '20141024',
                'uploader_id': 'Buddhanz1',
                'description': 'He likes to stay in shape with his heavy bag, he wont stop until its on the ground\n\nFollow Angry Ram on Facebook for regular updates -\nhttps://www.facebook.com/pages/Angry-Ram/1436897249899558?ref=hl',
                'uploader': 'Buddhanz',
                'title': 'Angry Ram destroys a punching bag',
            }
        }]
    }, {
        'url': 'http://www.buzzfeed.com/sheridanwatson/look-at-this-cute-dog-omg?utm_term=4ldqpia',
        'params': {
            'skip_download': True,  # Got enough YouTube download tests
        },
        'info_dict': {
            'id': 'look-at-this-cute-dog-omg',
            'description': 're:Munchkin the Teddy Bear is back ?!',
            'title': 'You Need To Stop What You\'re Doing And Watching This Dog Walk On A Treadmill',
        },
        'playlist': [{
            'info_dict': {
                'id': 'mVmBL8B-In0',
                'ext': 'mp4',
                'upload_date': '20141124',
                'uploader_id': 'CindysMunchkin',
                'description': 're:© 2014 Munchkin the',
                'uploader': 're:^Munchkin the',
                'title': 're:Munchkin the Teddy Bear gets her exercise',
            },
        }]
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)

        all_buckets = re.findall(
            r'(?s)<div class="video-embed[^"]*"..*?rel:bf_bucket_data=\'([^\']+)\'',
            webpage)

        entries = []
        for bd_json in all_buckets:
            bd = json.loads(bd_json)
            video = bd.get('video') or bd.get('progload_video')
            if not video:
                continue
            entries.append(self.url_result(video['url']))

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'entries': entries,
        }
