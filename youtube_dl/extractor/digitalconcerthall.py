# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


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
        MAX_TITLE_LENGTH = 128
        language, video_id = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        self.debug_out("url: " + url + " video_id: " + video_id + " language: " + language)
        webpage = self._download_webpage(url, video_id)
        playlist_title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title') or \
            self._og_search_title(webpage)
        self.debug_out("playlist_title: " + playlist_title)

        # this returns JSON containing the urls of the playlist
        # Note:  you must be authenticated to get the stream info
        playlist_dict = self._download_json(
            'https://www.digitalconcerthall.com/json_services/get_stream_urls?id='
            + video_id + "&language=" + language, video_id, note='Downloading Stream JSON').get('urls')
        # use the API to get other information about the concert
        vid_info_dict = self._download_json(
            'https://api.digitalconcerthall.com/v2/concert/'
            + video_id, video_id, headers={'Accept': 'application/json',
                                           'Accept-Language': language}).get('_embedded')

        entries = []
        for key in playlist_dict:
            self.debug_out("key: " + key)
            m3u8_url = playlist_dict.get(key)[0].get('url')
            self.debug_out("key url: " + m3u8_url)
            formats = self._extract_m3u8_formats(
                m3u8_url, key, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
            self.debug_out(formats)
            title = [vid_info_dict.get(x)[0].get('title', "unknown title") for x in vid_info_dict
                     if vid_info_dict.get(x)[0].get('id') == key][0]
            # avoid filenames that exceed filesystem limits
            title = (title[:MAX_TITLE_LENGTH] + '..') if len(title) > MAX_TITLE_LENGTH else title
            self.debug_out("title: " + title)
            entries.append({
                'id': key,
                'title': title,
                'url': m3u8_url,
                'formats': formats,
            })

        return {
            '_type': 'playlist',
            'id': video_id,
            'title': playlist_title,
            'entries': entries,
        }
