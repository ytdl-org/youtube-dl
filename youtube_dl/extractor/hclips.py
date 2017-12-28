# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor, ExtractorError


class HclipsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hclips\.com/videos/(?P<id>[a-zA-Z0-9-_]+)/?'
    _TEST = {
        'url': 'https://www.hclips.com/videos/hottest-homemade-movie-with-milf-brunette-scenes28529/',
        'md5': '9f4b205e68340cb8eed5a52d96301fd3',
        'info_dict': {
            'id': '1214901',
            'display_id': 'hottest-homemade-movie-with-milf-brunette-scenes28529',
            'ext': 'mp4',
            'title': 'Hottest Homemade movie with MILF, Brunette scenes',
            'age_limit': 18,
        }
    }

    def decode_hclips_video_url(self, encoded_url):
        # Warning: Contains cyrillic unicode
        decode_table = "АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~"
        last_char = len(decode_table) - 1
        decoded_url = ""
        for i in range(0, len(encoded_url), 4):
            a = decode_table.index(encoded_url[i + 0])
            b = decode_table.index(encoded_url[i + 1])
            c = decode_table.index(encoded_url[i + 2])
            d = decode_table.index(encoded_url[i + 3])

            decoded_url += chr((a << 2) | (b >> 4))

            if c != last_char:
                decoded_url += chr((b & 0xf) << 4 | c >> 2)

            if d != last_char:
                decoded_url += chr((c & 0x3) << 6 | d)

        if not decoded_url.startswith("http"):
            raise ExtractorError("Expected URL after decode. Got {}".format(decoded_url))

        return decoded_url

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        video_id = self._html_search_regex(r'https://www.hclips.com/embed/([0-9]*)', webpage, 'id_number', default=display_id)

        title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage, 'title', default=display_id)

        encoded_video_url = self._search_regex(r'var video_url="(.*?)"', webpage, 'video_url')
        video_url = self.decode_hclips_video_url(encoded_video_url)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'url': video_url,
            'age_limit': 18,
        }
