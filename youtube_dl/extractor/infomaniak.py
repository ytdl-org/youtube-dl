# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
import json


class InfomaniakVOD2IE(InfoExtractor):
    _VALID_URL = r'https?://player\.vod2\.infomaniak\.com/embed/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'https://player.vod2.infomaniak.com/embed/1jhvl2uq7kr4y',
        'md5': 'd06fb3fc5a8d7cb4d6e4a0f4e7c5a76a',
        'info_dict': {
            'id': '1jhvl2uq7kr4y',
            'ext': 'mp4',
            'title': 'RolandCarey2016-05-04.mp4',
            'description': '',
            'thumbnail': 'https://res.vod2.infomaniak.com/1/vod/thumbnail/1jhvl2uq8yqqv.jpg',
            'duration': 221,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # no useful data in given url, formatted url below reveals json data
        data_url = "https://res.vod2.infomaniak.com/{}/vod/share/{}".format(video_id[0], video_id)
        webpage = self._download_webpage(data_url, video_id)

        data = json.loads(webpage)['data']['media'][0]

        url = data['source']['url']
        title = data['title']
        description = ''
        thumbnail = data['image']['url']
        duration = data['duration']

        video_mimetype = data['source']['mimetype']

        info_dict = {
            'id': video_id,
            'url': url,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
        }

        # if file is m3u8
        if video_mimetype == 'application/x-mpegurl':
            info_dict['protocol'] = 'm3u8_native'
            info_dict['manifest_url'] = url

        return info_dict
