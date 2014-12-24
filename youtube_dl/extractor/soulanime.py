from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse
)


class SoulAnimeBaseIE(InfoExtractor):
    _VID_VALID_URL = r'http://[w.]*soul-anime\.(?P<domain>[^/]+)/watch[^/]*/(?P<id>[^/]+)'

    _VIDEO_URL_REGEX = r'<div id="download">[^<]*<a href="(?P<url>[^"]+)"'

    def _down_vid(self, url):
        mobj = re.match(self._VID_VALID_URL, url)
        video_id = mobj.group('id')
        domain = mobj.group('domain')

        page = self._download_webpage(url, video_id, "Downloading video page")

        video_url_encoded = self._html_search_regex(self._VIDEO_URL_REGEX, page, 'url', fatal=True)
        video_url = "http://www.soul-anime." + domain + video_url_encoded

        vid = self._request_webpage(video_url, video_id)
        #ext = vid.getheader("Content-Type").split("/")[1]
        ext = vid.info().gettype().split("/")[1]

        return {
            'id': video_id,
            'url': video_url,
            'ext': ext,
            'title': video_id,
            'description': video_id
        }


class SoulAnimeWatchingIE(SoulAnimeBaseIE):
    IE_NAME = "soulanime:watching"
    IE_DESC = "SoulAnime Watching"

    _VALID_URL = SoulAnimeBaseIE._VID_VALID_URL

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

    def _real_extract(self, url):
        return self._down_vid(url)


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
