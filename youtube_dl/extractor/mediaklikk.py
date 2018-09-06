# coding: utf-8
from __future__ import unicode_literals
import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote
)


class MediaKlikkIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mediaklikk\.hu/video/(?:[^/]+/)'
    _TESTS = [
        {
            'url': 'https://www.mediaklikk.hu/video/az-evszakok-buvoleteben-osz/',
            'info_dict': {
                'id': '2512015',
                'title': 'Az évszakok bűvöletében, Ősz',
                'series': 'Az évszakok bűvöletében',
                'ext': 'mp4'
            }
        },
        {
            'url': 'https://www.mediaklikk.hu/video/sporthirado-350-resz/',
            'info_dict': {
                'id': '2523053',
                'title': 'Sporthíradó, 350. rész',
                'series': 'Sporthíradó',
                'ext': 'mp4'
            }
        },
    ]

    def _real_extract(self, url):
        webpage = self._download_webpage(url,
                                         None,
                                         note='Fetching page')
        pattern = r"mtva_player_manager\.player\(document.getElementById\(.*\),(.*)\);"
        info_json = self._html_search_regex(pattern, webpage, 'info_json')
        info_meta = self._parse_json(compat_urllib_parse_unquote(info_json),
                                     None)
        video_id = str(info_meta['contentId']).decode('utf-8')
        info_ret = {
            '_type': 'video',
            'title': info_meta['title'],
            'ext': 'mp4',
            'id': video_id
        }
        if 'series' in info_meta:
            info_ret['series'] = info_meta['series']
        info_meta['video'] = info_meta['token']
        del info_meta['token']
        playerpage = self._download_webpage('https://player.mediaklikk.hu/playernew/player.php', video_id, note='Downloading player page', query=info_meta)
        pattern = r"\"file\": \"(.*)\","
        playlist_url = 'https:' + compat_urllib_parse_unquote(
            self._html_search_regex(pattern, playerpage, 'playlist_url'))\
            .replace('\\/', '/')
        formats = self._extract_wowza_formats(
            playlist_url, video_id, skip_protocols=['f4m', 'smil', 'dash'])
        self._sort_formats(formats)
        info_ret['formats'] = formats
        return info_ret
