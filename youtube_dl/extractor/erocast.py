# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ErocastIE(InfoExtractor):
    IE_NAME = 'erocast'
    _VALID_URL = r'https?://(?:www\.)?erocast\.me/track/(?P<id>[0-9]+)/(?P<display_id>[0-9a-zA-Z_-]+)'
    _TEST = {
        'url': 'https://erocast.me/track/6508/piano-sample-by-ytdl',
        'md5': '6764726b2d19161e93c9cf3a9a69800a',
        'info_dict': {
            'id': '6508',
            'ext': 'mp4',
            'title': 'Piano sample by ytdl',
            'uploader': 'ytdl',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # The Song data is in a script tag with the following format:
        # (see https://github.com/ytdl-org/youtube-dl/issues/31203#issuecomment-1259867716)
        searchPattern = r'<script>var song_data_' + str(video_id) + r' = (.+?)<\/script>'
        jsonString = self._html_search_regex(searchPattern, webpage, 'data')

        # The data is in JSON format, so we convert the JSON String to a python object
        # and read the data from this json object
        jsonObject = self._parse_json(jsonString, None, fatal=False)
        audio_url = jsonObject['stream_url']
        title = jsonObject['title']
        user_name = jsonObject['user']['name']

        # The audio url is a m3u8 playlist, so we extract the audio url from this playlist
        formats = []
        formats.extend(self._extract_m3u8_formats(
            audio_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls', fatal=False))

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'uploader': user_name,
        }
