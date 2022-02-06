# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class StreamFFIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?streamff\.com/v/(?P<id>[0-9a-zA-Z]+)'
    _TEST = {
        'url': 'https://streamff.com/v/bc22b8',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '42',
            'ext': 'mp4',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        response = self._download_json("https://streamff.com/api/videos/%s" % video_id, video_id)
        external_link = response["externalLink"]
        return self.url_result(external_link, ie="Generic")
