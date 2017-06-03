# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class JkAnimeIE(InfoExtractor):
    _VALID_URL = r'http://jkanime\.net/(?P<serie>[a-zA-Z0-9-_]+)/(?P<id>[a-zA-Z0-9_]+)'
    IE_DESC = 'JkAnime'
    _TEST = {
        'url': 'http://jkanime.net/dragon-ball-super/1/',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '1',
            'ext': 'mp4',
            'title': 'Video title goes here',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<title>\s*(.*)\s*</title>', webpage, 'title')
        # for example: 'https://jkanime.net/jk.php?u=stream/jkmedia/5b5b613c768162c54e3bba9ffb07e264/a28e5f284a491ba9f012bd30c66f58ee/1/2b6337dd852fc37524ff5147f21ef36b/',
        video_url = self._html_search_regex(r'<iframe class=\"player_conte\" src=\"(?P<id>[a-zA-Z0-9-/:.?=]+)', webpage, 'url')
        video_url = video_url.replace('jk.php?u=', '')        
        return {
            'id': video_id,
            'title': title,
            'url': video_url,
            'ext': 'mp4',
            'description': self._og_search_description(webpage),
            'uploader': self._search_regex(r'<div[^>]+id="uploader"[^>]*>([^<]+)<', webpage, 'uploader', fatal=False),
        }