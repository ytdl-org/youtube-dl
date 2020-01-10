# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
)


class TVNoeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tvnoe\.cz/porad/(?P<id>[-0-9a-z]+)'
    _TEST = {
        'url': 'https://www.tvnoe.cz/porad/26011-terra-santa-news-13-11-2019',
        'info_dict': {
            'id': '26011-terra-santa-news-13-11-2019',
            'ext': 'mp4',
            'series': 'Terra Santa News',
            'title': '13. 11. 2019',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        formats = []
        hls_url = self._search_regex(
            r"\s*src:\s*\'(?P<url>https?://[^\']+playlist.m3u8)\',", webpage, 'm3u8', fatal=False)
        if hls_url:
            dash_url = self._search_regex(
                r"\s*src:\s*\'(?P<url>https?://[^\']+manifest.mpd)\',", webpage, 'mpd', fatal=False)
        else:
            dash_url = self._search_regex(
                r"\s*src:\s*\'(?P<url>https?://[^\']+manifest.mpd)\',", webpage, 'mpd')

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
            r"<h2>(?P<title>.*)<\/h2>", webpage, 'title'))
        series = clean_html(self._search_regex(
            r"<h1>(?P<series>.*)<\/h1>", webpage, 'series'))
        return {
            'id': video_id,
            'title': title,
            'series': series,
            'formats': formats
        }
