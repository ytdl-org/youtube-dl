# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SfDebrisIE(InfoExtractor):
    _VALID_URL = r'http://sfdebris\.com/videos/[a-z]+/(?P<id>[a-z0-9\-]+)\.php'
    _TEST = {
        'url': 'http://sfdebris.com/videos/animation/transformerss1e01.php',
        'info_dict': {
            'id': 'sfdebris-560c327f4d852',
            'ext': 'mp4',
            'title': 'Transformers: More Than Meets the Eye 1'
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        playerdata_url = self._search_regex(
            r"src='(http://player\d?\.screenwavemedia\.com/(?:play/)?[a-zA-Z]+\.php\?[^']*\bid=.+?)'",
            webpage, 'player data URL')

        video_title = self._html_search_regex(
            r'<div class="vidtitle">\s*<h1>(?P<title>.+?)</h1>\s*</div>',
            webpage, 'title')

        return {
            '_type': 'url_transparent',
            'display_id': display_id,
            'title': video_title,
            'url': playerdata_url,
        }
