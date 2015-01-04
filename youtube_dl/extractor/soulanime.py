from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    HEADRequest,
    urlhandle_detect_ext,
)


class SoulAnimeWatchingIE(InfoExtractor):
    IE_NAME = "soulanime:watching"
    IE_DESC = "SoulAnime video"
    _TEST = {
        'url': 'http://www.soul-anime.net/watching/seirei-tsukai-no-blade-dance-episode-9/',
        'md5': '05fae04abf72298098b528e98abf4298',
        'info_dict': {
            'id': 'seirei-tsukai-no-blade-dance-episode-9',
            'ext': 'mp4',
            'title': 'seirei-tsukai-no-blade-dance-episode-9',
            'description': 'seirei-tsukai-no-blade-dance-episode-9'
        }
    }
    _VALID_URL = r'http://[w.]*soul-anime\.(?P<domain>[^/]+)/watch[^/]*/(?P<id>[^/]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        domain = mobj.group('domain')

        page = self._download_webpage(url, video_id)

        video_url_encoded = self._html_search_regex(
            r'<div id="download">[^<]*<a href="(?P<url>[^"]+)"', page, 'url')
        video_url = "http://www.soul-anime." + domain + video_url_encoded

        ext_req = HEADRequest(video_url)
        ext_handle = self._request_webpage(
            ext_req, video_id, note='Determining extension')
        ext = urlhandle_detect_ext(ext_handle)

        return {
            'id': video_id,
            'url': video_url,
            'ext': ext,
            'title': video_id,
            'description': video_id
        }


class SoulAnimeSeriesIE(InfoExtractor):
    IE_NAME = "soulanime:series"
    IE_DESC = "SoulAnime Series"

    _VALID_URL = r'http://[w.]*soul-anime\.(?P<domain>[^/]+)/anime./(?P<id>[^/]+)'

    _EPISODE_REGEX = r'<option value="(/watch[^/]*/[^"]+)">[^<]*</option>'

    _TEST = {
        'url': 'http://www.soul-anime.net/anime1/black-rock-shooter-tv/',
        'info_dict': {
            'id': 'black-rock-shooter-tv'
        },
        'playlist_count': 8
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        series_id = mobj.group('id')
        domain = mobj.group('domain')

        pattern = re.compile(self._EPISODE_REGEX)

        page = self._download_webpage(url, series_id, "Downloading series page")
        mobj = pattern.findall(page)

        entries = [self.url_result("http://www.soul-anime." + domain + obj) for obj in mobj]

        return self.playlist_result(entries, series_id)
