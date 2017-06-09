# coding: utf-8

from __future__ import unicode_literals


import re


from .common import InfoExtractor


class AnimevostIE(InfoExtractor):
    _TESTS = [{
        'url': 'http://animevost.org/tip/tv/1864-renai-boukun.html',
        'info_dict': {
            'title': 'Любовь тирана / Renai Boukun',
            'id': '1864',
        },
        'playlist_mincount': 10,
    }, {

        'url': 'http://animevost.org/tip/tv-speshl/1854-ryuu-no-haisha.html',
        'info_dict': {
            'title': 'Драконий дантист / Ryuu no Haisha',
            'id': '1854',
        },
        'playlist_mincount': 2,
    }, {

        'url': 'http://animevost.org/tip/ova/1741-mahou-tsukai-no-yome-hoshi-matsu-hito.html',
        'info_dict': {
            'title': 'Невеста чародея / Mahou Tsukai no Yome: Hoshi Matsu Hito',
            'id': '1741',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'http://animevost.org/tip/ona/1797-huyao-xiao-hongniang.html',
        'info_dict': {
            'title': 'Сводники духов: Лисьи свахи / Huyao Xiao Hongniang',
            'id': '1797',
        },
        'playlist_mincount': 57,
    }]

    _VALID_URL = r'http://animevost\.org/tip/[-\w\d]+/(\d+)-[-\w\d]+\.html'
    _TITLE_PATTERN = r'<meta property="og:title" content="([-\s\d\w/:]+)\['
    _DATA_PATTERN = r'var data = \{([-\d\w\s,":]+),};'

    def _real_extract(self, url):
        anime_id = self._search_regex(self._VALID_URL, url, 'anime id', flags=re.UNICODE)

        anime_page = self._download_webpage(url, anime_id)
        anime_title = self._html_search_regex(self._TITLE_PATTERN, anime_page, 'anime title', flags=re.UNICODE)

        data_str = self._html_search_regex(self._DATA_PATTERN, anime_page, 'anime series', flags=re.UNICODE)
        data = self._parse_json("{%s}" % data_str, '')

        entries = self.__entries(data, anime_title)
        return self.playlist_result(entries, anime_id, anime_title)

    def __entries(self, data, anime_title):
        for ename, eid in data.items():
            entry_url = 'animevost-entry://%s' % eid
            full_title = '%s - %s' % (anime_title, ename)
            yield self.url_result(entry_url, 'AnimevostEntry', eid, full_title)


class AnimevostEntryIE(InfoExtractor):
    _VALID_URL = r'animevost-entry://(.+)'
    _PLAYER_URL_PATTERN = r'http://play.aniland.org/%s?player=3'
    _FLASHVARS_PATTERN = r'var flashvars = \{([":\d\w\s,/.+=-]+)};'

    def _real_extract(self, url):
        eid = url.split('/')[-1]

        player_url = self._PLAYER_URL_PATTERN % eid
        player_page = self._download_webpage(player_url, eid)

        files_str = self._html_search_regex(self._FLASHVARS_PATTERN, player_page, 'flash vars', flags=re.UNICODE)
        files = self._parse_json("{%s}" % files_str, eid)

        raw_url = files['filehd'] if 'filehd' in files else files['file']
        video_url = raw_url.partition(":hls")[0]

        return {
            'id': eid,
            'url': video_url,
            'ext': 'mp4',
            'title': eid,
        }
