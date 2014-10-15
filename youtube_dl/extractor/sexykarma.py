# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class SexyKarmaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexykarma\.com/gonewild/video/(?P<id>[a-zA-Z0-9\-]+)(.html)'
    _TESTS = [{
        'url': 'http://www.sexykarma.com/gonewild/video/taking-a-quick-pee-yHI70cOyIHt.html',
        'md5': 'b9798e7d1ef1765116a8f516c8091dbd',
        'info_dict': {
            'id': 'taking-a-quick-pee-yHI70cOyIHt',
            'ext': 'mp4',
            'title': 'Taking a quick pee.',
            'uploader': 'wildginger7',
        }
    }, {
        'url': 'http://www.sexykarma.com/gonewild/video/pot-pixie-tribute-8Id6EZPbuHf.html',
        'md5': 'dd216c68d29b49b12842b9babe762a5d',
        'info_dict': {
            'id': 'pot-pixie-tribute-8Id6EZPbuHf',
            'ext': 'mp4',
            'title': 'pot_pixie tribute',
            'uploader': 'banffite',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # TODO more code goes here, for example ...
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<h2 class="he2"><span>(.*?)</span>', webpage, 'title')
        uploader = self._html_search_regex(r'class="aupa">\n*(.*?)</a>', webpage, 'uploader')
        url = self._html_search_regex(r'<p><a href="(.*?)" ?\n*target="_blank"><font color', webpage, 'url')

        return {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'url': url
        }
