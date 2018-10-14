# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SonosFmIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sonus\.fm/on-demand/(?P<id>[0-9_a-z-]+)'
    _TEST = {
        'url': 'http://sonus.fm/on-demand/4033_reifeprufung-dj-contest-live-stream',
        'md5': 'fd2386c8477754087ddd4c905422e192',
        'info_dict': {
            'id': '4033_reifeprufung-dj-contest-live-stream',
            'ext': 'm3u8',
            'title': 'Reifeprüfung DJ Contest LIVE Stream - sonus.fm',
            'thumbnail': 'http://sonus.fm/img/shows/311385913007047.jpg',
            'description': 'md5:befa45b98c2952225effd2d7de806c38'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_url = self._html_search_regex(r'<meta property=\"og:video\" content=\"(.*)\"/>', webpage, 'player_url')
        file_name = self._search_regex(
            r'https://www.sonus.fm/jwplayer/player.swf\?file=mp4:([A-z0-9-.]*)&',
            player_url,
            'file_name'
        ).replace('.mov', '.mp4')
        m3u8_playlist = 'http://www.sonus.fm:1935/vod/mp4:{file}/playlist.m3u8'.format(file=file_name)

        return {
            'id': video_id,
            'title': self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title'),
            'description': self._og_search_description(webpage),
            'url': m3u8_playlist,
            'thumbnail': self._html_search_regex(r'<meta property=\"og:image\" content=\"(.*)\"\s?/>', webpage, 'image')
        }
