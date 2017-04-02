# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class VShareIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vshare\.io/(?:(?:d)|(?P<v>v))/(?P<id>.+)(?(v)/width-\d+/height-\d+/\d+)'
    _TESTS = [{
        'url': 'https://vshare.io/d/0f64ce6',
        'md5': '16d7b8fef58846db47419199ff1ab3e7',
        'info_dict': {
            'id': '0f64ce6',
            'title': 'vl14062007715967',
            'ext': 'mp4',
        }
    }, {
        'url': 'https://vshare.io/v/0f64ce6/width-650/height-430/1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        i = url.find('/v/')
        if not i == -1:
            url = url[:i] + '/d/' + video_id
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<div id="root-container">\s*<div id[^>]+>\s*(.+?)<br/>', webpage, 'title')
        video_url = self._search_regex(r'<a[^>]+href="(https?://s\d+\.vshare\.io/download.+?)">Click here</a>', webpage, 'video url')

        return {
            'id': video_id,
            'title': title,
            'url': video_url,
        }
