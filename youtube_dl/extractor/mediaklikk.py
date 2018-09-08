# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse_unquote,
    compat_str
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
                'display_id': 'az-evszakok-buvoleteben-osz',
                'ext': 'mp4'
            }
        },
        {
            'url': 'https://www.mediaklikk.hu/video/sporthirado-350-resz/',
            'info_dict': {
                'id': '2523053',
                'title': 'Sporthíradó, 350. rész',
                'series': 'Sporthíradó',
                'display_id': 'sporthirado-350-resz',
                'ext': 'mp4'
            }
        },
    ]

    def _real_extract(self, url):
        webpage = self._download_webpage(url,
                                         None)
        
        pattern = r"mtva_player_manager\.player\(document.getElementById\(.*\),\s?(\{.*\}).*\);"
        info_json = self._html_search_regex(pattern, webpage, 'info_json')
        info_meta = self._parse_json(compat_urllib_parse_unquote(info_json),
                                     None)
        pattern = r"https?://(?:www\.)?mediaklikk\.hu/video/([a-z\-0-9]+)/?"
        display_id = self._search_regex(pattern, url, 'display_id')
        video_id = compat_str(info_meta['contentId'])
        info_ret = {
            '_type': 'video',
            'title': info_meta.get('title') or self._og_search_title(webpage),
            'ext': 'mp4',
            'display_id': display_id,
            'id': video_id
        }
        if 'series' in info_meta:
            info_ret['series'] = info_meta['series']
        info_meta['video'] = info_meta['token']
        del info_meta['token']
        playerpage = self._download_webpage('https://player.mediaklikk.hu/playernew/player.php',
                                            video_id,
                                            query=info_meta)
        pattern = r"\"file\": \"(\\/\\/.*playlist\.m3u8)\","
        playlist_url = 'https:' + compat_urllib_parse_unquote(
            self._html_search_regex(pattern, playerpage, 'playlist_url'))\
            .replace('\\/', '/')
        formats = self._extract_wowza_formats(
            playlist_url, video_id, skip_protocols=['f4m', 'smil', 'dash'])
        self._sort_formats(formats)
        info_ret['formats'] = formats
        return info_ret
