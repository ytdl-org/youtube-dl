# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import try_get


class GramofonOnlineIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gramofononline\.hu/(?:hu/|en/|de/)?(?:listen.php\?.*track=)?(?P<id>[0-9]+)'

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
        # same as above but with         /en/
        'url': 'https://gramofononline.hu/en/1401835664/papageno-duett',
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
    }, {
        # same as above but with         /en/
        'url': 'https://gramofononline.hu/en/listen.php?autoplay=true&track=1401835664',
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

    def _get_entry(self, obj, webpage):
        id1 = (obj.get('id')
               or self._search_regex(r'var\s*track=([^;]+);', webpage, 'id', default=None)
               or self._search_regex(r'http://gramofononline\.hu/flash/loader\.swf\?id=(\w+)', webpage, 'id'))
        url_suffix = (obj.get('source')
                      or self._search_regex(r'/data\.php\?n=600&amp;fname=(\w+)', webpage, 'url_suffix', default=None)
                      or self._search_regex(r'http://gramofononline\.hu/keyframe/go/midres/midres_(\w+)', webpage, 'url_suffix'))
        title = (obj.get('name')
                 or self._html_search_regex(r'<title>Gramofon Online / (.*)</title>', webpage, 'title')
                 or self._og_search_title(webpage))
        artist = obj.get('artist')
        return get_gramofon_online_info_dict(id1, title, url_suffix, artist)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        json_tracklist = self._search_regex(r'var\s+trackList\s*=\s*(\[.*\]);', webpage, 'json_tracklist')
        lineobjs = self._parse_json(json_tracklist, video_id, transform_source=None, fatal=False) or {}
        obj = try_get(lineobjs, lambda x: x[0]) or {}
        return self._get_entry(obj, webpage)


class GramofonOnlinePlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gramofononline\.hu(?:/(?:hu/|en/|de/)?(?:index.php?.*playradio.*)?)?$'

    _TESTS = [{
        'url': 'https://gramofononline.hu',
        'only_matching': True
    }, {
        'url': 'https://gramofononline.hu/',
        'only_matching': True
    }, {
        'url': 'https://gramofononline.hu/en/',
        'only_matching': True
    }, {
        'url': 'https://gramofononline.hu/index.php?playradio=ord%3D7%26w%3D2&autoplay=1',
        'only_matching': True
    }, {
        'url': 'https://gramofononline.hu/en/index.php?playradio=ord%3D7%26w%3D2&autoplay=1',
        'only_matching': True
    }]

    def _get_entry(self, obj):
        id1 = obj['id']
        url_suffix = obj['source']
        title = obj['name']
        artist = obj.get('artist')
        return get_gramofon_online_info_dict(id1, title, url_suffix, artist)

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url)

        json_tracklist = self._search_regex(r'var\s+trackList\s*=\s*(\[.*\]);', webpage, 'json_tracklist')
        lineobjs = self._parse_json(json_tracklist, url)

        return {
            '_type': 'playlist',
            'entries': [self._get_entry(obj) for obj in lineobjs]
        }


def get_gramofon_online_info_dict(id1, title, url_suffix, artist):
    return {
        'id': id1,
        'title': title,
        'http_headers': {'Referer': 'https://gramofononline.hu/' + id1},
        'artist': artist,
        'thumbnail': 'https://gramofononline.hu/getImage.php?id=' + url_suffix,
        'formats': [{
            'url': 'https://gramofononline.hu/go/master/' + url_suffix + '.mp3',
            'ext': 'mp3'
        }, {
            'url': 'https://gramofononline.hu/go/noise_reduction/' + url_suffix + '.mp3',
            'ext': 'mp3'
        }]
    }
