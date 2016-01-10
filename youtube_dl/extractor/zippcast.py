# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ZippCastIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?zippcast\.com/video/(?P<id>[0-9a-zA-Z]+)'
    _TESTS = [{
        'url': 'http://www.zippcast.com/video/c9cfd5c7e44dbc29c81',
        'md5': 'f2aea8659962d9155031aaeac53f7c54',
        'info_dict': {
            'id': 'c9cfd5c7e44dbc29c81',
            'ext': 'mp4',
            'title': '[Vinesauce] Vinny - Digital Space Traveler',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'vinesauce',
            'description': 'Muted on youtube, but now uploaded in it\'s original form.',
            'categories': ['Entertainment'],
            'view_count': int,
        },
    }, {
        'url': 'http://www.zippcast.com/video/b79c0a233e9c6581775',
        'md5': 'b8631f0cc48ed15387f9179988d0c97c',
        'info_dict': {
            'id': 'b79c0a233e9c6581775',
            'ext': 'mp4',
            'title': 'Battlefield Hardline Trailer',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'IGXGaming',
            'description': 'Battlefield Hardline Trailer',
            'categories': ['Gaming'],
            'view_count': int,
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'title="(.+?)"', webpage, 'title')
        uploader = self._html_search_regex(r'http://www.zippcast.com/profile/(.+?)">', webpage, 'uploader')
        url = self._html_search_regex(r'<source src="(.+?)" type="', webpage, 'url')
        description = self._html_search_regex(r'<span class="vdescr".+>(.+?)</span>', webpage, 'description')
        thumbnail = self._html_search_regex(r'poster="(.+?)" controls>', webpage, 'thumbnail')
        categories = self._html_search_regex(r'<a href="http://www.zippcast.com/categories/(.+?)"', webpage, 'categories')
        view_count = self._html_search_regex(r'<td align="right"><h3>(.+?) views!', webpage, 'view_count')

        return {
            'id': video_id,
            'title': title,
            'url': url,
            'description': description,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'categories': [categories],
            'view_count': int(view_count.replace(',', '')),
        }
