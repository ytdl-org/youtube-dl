# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ClickholeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?clickhole\.com/video/[a-z\-]+(?P<id>[\d]+)'
    _TEST = {
        'url': 'http://www.clickhole.com/video/dont-understand-bitcoin-man-will-mumble-explanatio-2537',
        'md5': '74229b82e3ffde84b6e11dcadcd3d237',
        'info_dict': {
            'id': '2537',
            'ext': 'mp4',
            'title': 'Don’t Understand Bitcoin? This Man Will Mumble An Explanation At You',
            'description': 'Click, watch, share',
            'thumbnail': 're:^https?://.*\.jpg$'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # Find the embedded iframe
        embedded_url = self._search_regex(
            r'<iframe name="embedded".*src="//(.*)&.+">', webpage, 'embedded_url')
        embed_page = self._download_webpage('http://' + embedded_url, video_id)
        # Extract the videos from the iframe
        mp4_video = self._search_regex(
            r'<source src="(.*\.mp4)" type=.video/mp4. />', embed_page, 'video_url')
        webm_video = self._search_regex(
            r'<source src="(.*\.webm)" type=.video/webm. />', embed_page, 'video_url')

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': [{'url': webm_video}, {'url': mp4_video}],
        }
