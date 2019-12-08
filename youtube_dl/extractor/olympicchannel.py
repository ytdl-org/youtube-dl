# coding: utf-8
from __future__ import unicode_literals

import re
from .common import InfoExtractor


class OlympicChannelIE(InfoExtractor):
    _VALID_URL = r"http(?:s)?://(\w+)\.?olympicchannel.com/../video/detail/(?P<id>.*)/"
    _TEST = {
        'url': 'https://www.olympicchannel.com/en/video/detail/women-s-downhill-2-fis-world-cup-lake-louise/',
        'info_dict': {
            'id': 'women-s-downhill-2-fis-world-cup-lake-louise',
            'ext': 'mp4',
            'title': "Women's Downhill 2 | FIS World Cup - Lake Louise | Olympic Channel",
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        baseUrl = self._html_search_regex(r'meta name="video_url" content="(.*?)"', webpage, 'baseUrl')
        domainUrl = re.search(r'(http(?:s)?://.*?)/', baseUrl).group(0)

        url = self._download_webpage("https://www.olympicchannel.com/OcsTokenization/api/v1/tokenizedUrl?url=%s&domain=%s" % (baseUrl, domainUrl), video_id)

        formats = []
        formats.extend(self._extract_m3u8_formats(url.replace('"', ''), video_id, ext='mp4'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats
        }
