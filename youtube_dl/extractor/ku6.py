from __future__ import unicode_literals
import re

from .common import InfoExtractor


class Ku6IE(InfoExtractor):
    _VALID_URL = r'https?://www\.ku6\.com/[^/]+/[^\.]+\.html\?vid=(?P<id>[a-zA-Z0-9\-\_]+)'
    _TESTS = [{
        'url': 'http://www.ku6.com/2017/detail.html?vid=cJlL_h5g7wWOKKQ4fGXdvg',
        'md5': '52a37c7a99741911b9a08f141be1ee15',
        'info_dict': {
            'id': 'cJlL_h5g7wWOKKQ4fGXdvg',
            'ext': 'mp4',
            'title': '大吉成长记 第98集 金银小饰品',
        },
    }, {
        # found in webpage javascript
        'url': 'http://www.ku6.com/2017/detail-zt.html?vid=bb3s1AQX8uQqLCtPZmyd02',
        'md5': '1f4f977bbd935bbc51846bb543d9d1e7',
        'info_dict': {
            'id': 'bb3s1AQX8uQqLCtPZmyd02',
            'ext': 'mp4',
            'title': '“迎接十九大、忠诚保平安”综合实战演练暨誓师动员大会',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        json_data = self._download_json('http://ku6.51y5.net/detail.do?vid=%s' % video_id, video_id)

        if json_data['data']:
            return {
                'id': video_id,
                'title': json_data['data']['title'],
                'url': json_data['data']['video']['playUrl']
            }

        webpage = self._download_webpage(url, video_id)
        dataMap = self._html_search_regex(video_id + r':([^}]+})', webpage, 'dataMap')
        # add quote in JSON object keys
        dataMap = re.sub(r'([{,])([a-zA-Z]+)', r'\1"\2"', dataMap)
        json_data = self._parse_json(dataMap, video_id)
        return {
            'id': video_id,
            'title': json_data['title'],
            'url': json_data['playUrl']
        }
