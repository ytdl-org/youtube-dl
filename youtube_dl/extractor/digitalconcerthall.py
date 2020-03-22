# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    clean_html,
    get_element_by_id,
)


class DigitalConcertHallIE(InfoExtractor):
    IE_DESC = 'DigitalConcertHall extractor'
    _VALID_URL = r'https?://(?:www\.)?digitalconcerthall\.com/(?P<language>[a-z]+)/concert/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.digitalconcerthall.com/en/concert/51841',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '51841',
            'language': 'en',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*/images/core/Phil.*\.jpg$',
        }
    }

    def debug_out(self, args):
        if not self._downloader.params.get('verbose', False):
            return

        self.to_screen('[debug] %s' % args)

    def _real_extract(self, url):
        language, video_id = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        self.debug_out("url: " + url + " video_id: " + video_id + " language: " + language)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        self.to_screen("title: " + title)

        # this returns JSON containing the urls of the playlist
        playlist_dict = self._download_json(
            'https://www.digitalconcerthall.com/json_services/get_stream_urls?id=' + video_id + "&language=" + language, video_id).get('urls')

        entries = []
        for key in playlist_dict:
            self.debug_out("key: " + key)
            m3u8_url = playlist_dict.get(key)[0].get('url')
            self.debug_out("key url: " + m3u8_url)
            formats = self._extract_m3u8_formats(m3u8_url, key, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
            self.debug_out(formats)
            # the div with id=key contains the video title
            vid_info_div = clean_html(get_element_by_id(key, webpage))
            self.debug_out("vid_info_div:\n" + vid_info_div)
            title = re.sub(r'\s+', ' ', vid_info_div)
            self.to_screen("title: " + title)
            entries.append({
                'id': key,
                'title': title,
                'url': m3u8_url,
                'formats': formats,
            })

        return {
            '_type': 'playlist',
            'id': video_id,
            'title': title,
            'entries': entries,
        }
