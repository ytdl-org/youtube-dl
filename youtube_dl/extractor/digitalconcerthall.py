# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class DigitalConcertHallIE(InfoExtractor):
    IE_DESC = 'DigitalConcertHall extractor'
    _VALID_URL = r'https?://(?:www\.)?digitalconcerthall\.com/(?P<language>[a-z]+)/concert/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.digitalconcerthall.com/en/concert/51841',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '51841',
            'language': 'en',
            'ext': 'mp4',
            'title': 'Video title goes here',
            'thumbnail': r're:^https?://.*/images/core/Phil.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    },]

    def _real_extract(self, url):
        #video_id = self._match_id(url)
        language, video_id = re.match(self._VALID_URL, url).groups()
        if not language:
            language = 'en'
        print("url: ", url, " video_id: ", video_id, " language: ", language, "\n")
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>(.+?)</title>', webpage, 'title')
        print("title: ", title, "\n")

        # this returns JSON, which contains the urls of the playlist
        #video_data = self._download_webpage(
        #   'https://www.digitalconcerthall.com/json_services/get_stream_urls?id=' + video_id + "&language=" + language, video_id)
        playlist_dict = self._download_json(
            'https://www.digitalconcerthall.com/json_services/get_stream_urls?id=' + video_id + "&language=" + language, video_id)['urls']

        entries = []
        for key in playlist_dict:
            print("key: ", key, "\n")
            print("key url: ", playlist_dict[key][0]['url'], "\n")
            entries.append({
                'id': video_id,
                'title': title + "-" + key,
                'url': playlist_dict[key][0]['url'],
            })

#        for i in entries:
#            print(i)

        return {
            '_type': 'playlist',
            'id': video_id,
            'title': title,
            'entries': entries,
        }
