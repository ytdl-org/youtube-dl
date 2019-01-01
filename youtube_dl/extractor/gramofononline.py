# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import re
import json


class GramofonOnlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gramofononline\.hu(/(listen.php\?.*track=)?(?P<id>[0-9]+))?'

    _TESTS = [{
        'url': 'https://gramofononline.hu/1401835664/papageno-duett',
        'md5': '1b4bcabde313f09cdd48c463b54d8125',
        'info_dict': {
            'id': '1401835664',
            'title': 'Papageno-Duett ',
            'artist': 'Johanna Gadski, Otto Goritz, ismeretlen zenekar',
            'ext': 'mp3'
        }
    }, {
        'url': 'https://gramofononline.hu/listen.php?autoplay=true&track=1401835664',
        'md5': '1b4bcabde313f09cdd48c463b54d8125',
        'info_dict': {
            'id': '1401835664',
            'title': 'Papageno-Duett ',
            'artist': 'Johanna Gadski, Otto Goritz, ismeretlen zenekar',
            'ext': 'mp3'
        },
        'params': {
            'skip_download': True,
        }
    }]

    def _get_entry(self, obj):
        id1 = obj.get("id")
        source = obj.get("source")
        name = obj.get("name")
        artist = obj.get("artist")
        # subname = obj.get("subname")
        # paralelname = obj.get("paralelname")
        # record = obj.get("record")
        # long1 = obj.get("long")
        # genre = obj.get("genre")
        # author = obj.get("author")
        # state = obj.get("state")
        # matrica = obj.get("matrica")
        # publisher = obj.get("publisher")
        # img = obj.get("img")
        return {
            'id': id1,
            'title': name,
            'http_headers': {'Referer': 'https://gramofononline.hu/' + id1},
            'artist': artist,
            'thumbnail': 'https://gramofononline.hu/getImage.php?id=' + source,
            'formats': [{
                'url': 'https://gramofononline.hu/go/master/' + source + '.mp3',
                'ext': 'mp3'
            }, {
                'url': 'https://gramofononline.hu/go/noise_reduction/' + source + '.mp3',
                'ext': 'mp3'
            }]
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        for line in webpage.split("\n"):
            m = re.search(r'var\s+trackList\s*=\s*(\[.*\]);?\s*', line)
            if m:
                break
        lineobjs = json.loads(m.group(1))

        if len(lineobjs) > 1:
            result = {
                '_type': 'playlist',
                'entries': [self._get_entry(obj) for obj in lineobjs]
            }
        else:
            result = self._get_entry(lineobjs[0])

        return result
