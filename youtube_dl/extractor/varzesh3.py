# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class Varzesh3IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?video\.varzesh3\.com/(?:[^/]+/)+(?P<id>[^/]+)/?'
    _TEST = {
        'url': 'http://video.varzesh3.com/germany/bundesliga/5-%D9%88%D8%A7%DA%A9%D9%86%D8%B4-%D8%A8%D8%B1%D8%AA%D8%B1-%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D9%87%E2%80%8C%D8%A8%D8%A7%D9%86%D8%A7%D9%86%D8%9B%D9%87%D9%81%D8%AA%D9%87-26-%D8%A8%D9%88%D9%86%D8%AF%D8%B3/',
        'md5': '2a933874cb7dce4366075281eb49e855',
        'info_dict': {
            'id': '76337',
            'ext': 'mp4',
            'title': '۵ واکنش برتر دروازه‌بانان؛هفته ۲۶ بوندسلیگا',
            'description': 'فصل ۲۰۱۵-۲۰۱۴',
            'thumbnail': 're:^https?://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        video_url = self._search_regex(
            r'<source[^>]+src="([^"]+)"', webpage, 'video url')

        title = self._og_search_title(webpage)
        description = self._html_search_regex(
            r'(?s)<div class="matn">(.+?)</div>',
            webpage, 'description', fatal=False)
        thumbnail = self._og_search_thumbnail(webpage)

        video_id = self._search_regex(
            r"<link[^>]+rel='(?:canonical|shortlink)'[^>]+href='/\?p=([^']+)'",
            webpage, display_id, default=display_id)

        return {
            'url': video_url,
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
        }
