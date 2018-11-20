# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

class NarandoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?narando\.com/articles/(?P<id>([a-zA-Z]|-)+)'
    _TEST = {
        'url': 'https://narando.com/articles/an-ihrem-selbstlob-erkennt-man-sie',
        'md5': 'd20f671f0395bab8f8285d1f6e8f965e',
        'info_dict': {
#            'id': 'b2t4t789kxgy9g7ms4rwjvvw', was being used as id previously, is internal video id
            'id': 'an-ihrem-selbstlob-erkennt-man-sie',
            'ext': 'mp3',
            'title': 'An  ihrem  Selbstlob  erkennt  man  sie',
            'url': 'https://static.narando.com/sounds/10492/original.mp3',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
#        webpage = self._download_webpage(url,"?")
#        print(url)
#        print('https://narando.com/articles/'+video_id)
        webpage = self._download_webpage('https://narando.com/articles/'+video_id+"?", video_id)#for some reason, this absolutely refused to work, so I'm negating the video_id and just adding it directly
        # TODO more code goes here, for example ...
        title = self._html_search_regex(r'<h1 class="visible-xs h3">(.+?)</h1>', webpage, 'title')
#        print(title)
        player_id = self._html_search_regex(" ".join(r'[\n\r].*https:\/\/narando.com\/r\/\s*([^"]*)'.split()), webpage, 'player_id')
        player_page = self._download_webpage('https://narando.com/widget?r='+player_id+'&',player_id)#same as above
        download_url = self._html_search_regex(r'.<div class="stream_url hide">\s*([^?]*)', player_page, 'mp3_ddl')
        return {
            'id': video_id,
            'title': title,
            'url': download_url,
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
