# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)
import re


class Varzesh3IE(InfoExtractor):
    _VALID_URL = r'(?P<url>(https?://(?:www\.)?video\.varzesh3\.com)/(?P<id>.+))'
    _TEST ={
        'url': 'http://video.varzesh3.com/germany/bundesliga/5-%D9%88%D8%A7%DA%A9%D9%86%D8%B4-%D8%A8%D8%B1%D8%AA%D8%B1-%D8%AF%D8%B1%D9%88%D8%A7%D8%B2%D9%87%E2%80%8C%D8%A8%D8%A7%D9%86%D8%A7%D9%86%D8%9B%D9%87%D9%81%D8%AA%D9%87-26-%D8%A8%D9%88%D9%86%D8%AF%D8%B3/',
        'md5': '2a933874cb7dce4366075281eb49e855',
        'info_dict': {
            'url': 'http://dl1.video.varzesh3.com/video/clip94/1/video/namayeshi/saves_week26.mp4',
            'id': '76337',
            'ext': 'mp4',
            'title': u'۵ واکنش برتر دروازه‌بانان؛هفته ۲۶ بوندسلیگا',
            'thumbnail': 'http://video.varzesh3.com/wp-content/uploads/230315_saves_week26.jpg',
            'description': u'فصل ۲۰۱۵-۲۰۱۴',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        if not 'shortlink' in webpage:
            raise ExtractorError('URL has no videos or there is a problem.')

        title = self._html_search_regex(r'meta[^>]+property="og:title"[^>]+content="([^"]+)"', webpage, 'title')
        video_link = self._html_search_regex(r'source[^>]+src="([^"]+)"', webpage, 'video_link')
        vid_id = self._html_search_regex(r"link[^>]+rel='canonical'[^>]+href='\/\?p=([^']+)'\/>", webpage, 'vid_id')
        try:
            description = self._html_search_regex(r'<div class="matn">(.*?)</div>', webpage, 'description', flags=re.DOTALL)
        except:
            description = title
        thumbnail = self._html_search_regex(r'link[^>]+rel="image_src"[^>]+href="([^"]+)"', webpage, 'thumbnail')

        return {
            'url': video_link,
            'id': vid_id,
            'title': title,
            'ext': video_link.split(".")[-1],
            'description': description,
            'thumbnail': thumbnail,
        }
