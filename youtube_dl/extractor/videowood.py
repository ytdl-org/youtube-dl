from __future__ import unicode_literals
from .common import InfoExtractor
import re


class VideoWoodIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?videowood\.tv/video/(?P<id>[\da-zA-Z]+)'
    _TEST = {
        'url': 'http://videowood.tv/video/cy3q',
        'md5': '0e98cba08c31f0d3153709926bca51ac',
        'info_dict': {
            'id': 'cy3q',
            'ext': 'mp4',
            'title': 'Between.S01E02.iTALiAN.subbed.avi'
        }}

    def _get_property(self, config, prop):
        c = self._search_regex(r'%s: \'(.+?)\',' % prop, config, 'prop %s' % prop)
        return c

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace('/video/', '/embed/')
        embed = self._download_webpage(url, video_id)
        jwconfig = self._search_regex(r'config += +(\{.*?\});', embed, 'metadata', flags=re.DOTALL)
        data = {'id': video_id}
        for s in [('file', 'url'), ('image', 'thumbnail'), ('title', 'title')]:
            data[s[1]] = self._get_property(jwconfig, s[0])
        return data
