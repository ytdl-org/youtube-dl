# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    url_or_none,
    js_to_json,
    try_get
)
from ..compat import (
    compat_str
)


class TVNoeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tvnoe\.cz/porad/(?P<id>[0-9]+).*'
    _TEST = {
        'url': 'https://www.tvnoe.cz/porad/26011-terra-santa-news-13-11-2019',
        'info_dict': {
            'id': '26011',
            'ext': 'mp4',
            'series': 'Terra Santa News',
            'title': '13. 11. 2019',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        formats = []
        json = self._search_regex(r'(?sm)var *INIT_PLAYER *= *(?P<json>[^;]+);', webpage, 'json')
        player_data = self._parse_json(json, video_id, js_to_json)
        hls_url = url_or_none(try_get(player_data,
                                      lambda x: x['tracks']['HLS'][0]['src'], compat_str))
        dash_url = url_or_none(try_get(player_data,
                                       lambda x: x['tracks']['DASH'][0]['src'], compat_str))

        if dash_url:
            formats.extend(self._extract_mpd_formats(
                dash_url, video_id, mpd_id='dash', fatal=False))
        if hls_url:
            if formats:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, video_id, ext='mp4', m3u8_id='hls', fatal=False))
            else:
                formats.extend(self._extract_m3u8_formats(
                    hls_url, video_id, ext='mp4', m3u8_id='hls'))

        self._sort_formats(formats)

        title = clean_html(self._search_regex(
            r'<h2>(?P<title>.+)<\/h2>', webpage, 'title', fatal=False))
        series = clean_html(self._search_regex(
            r'<h1>(?P<series>.+)<\/h1>', webpage, 'series', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'series': series,
            'formats': formats
        }
