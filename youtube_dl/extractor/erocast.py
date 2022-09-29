# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ErocastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?erocast\.me/track/(?P<id>[0-9]+)/([a-z]+-)+[a-z]+'
    _TEST = {
        'url': 'https://erocast.me/track/4254/intimate-morning-with-your-wife',
        'info_dict': {
            'id': '4254',
            'formats': [{'url': "https:\/\/erocast.s3.us-east-2.wasabisys.com\/261020\/track.m3u8", 'ext': 'hls'}],
            'ext': 'mp3'
            # TODO more properties, either as:
            # * A
            # value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json_data = self._search_regex(r'<script>(.+\n)', webpage, 'song data')
        json_data = json_data[json_data.find('{') - 1:].replace("</script>", "")
        json_data = self._parse_json(json_data, video_id)
        # TODO more code goes here, for example ...
        # title = self._html_search_regex(r'<script>(.|\n)+*}<\/script>', webpage, 'title')
        return {
            'id': video_id,
            'title': json_data["title"],
            'formats': [{'url': json_data['file_url'], 'ext': 'hls'}],
            'ext': 'mp3'
            # 'description': self._og_search_description(webpage),
            # 'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
