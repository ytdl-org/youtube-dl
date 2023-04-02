# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    traverse_obj,
    int_or_none,
    url_or_none,
)


class InfomaniakVOD2IE(InfoExtractor):
    _VALID_URL = r'https?://player\.vod2\.infomaniak\.com/embed/(?P<id>[^/?#&]+)'
    _TESTS = [
        # m3u8 test
        {
            'url': 'https://player.vod2.infomaniak.com/embed/1jhvl2uqg6ywp',
            'md5': 'b45c718f1d59869aac4caa82f4a7c386',
            'info_dict': {
                'id': '1jhvl2uqg6ywp',
                'ext': 'm3u8',
                'title': 'Conférence à Dyo, octobre 2022',
                'thumbnail': 'https://res.vod2.infomaniak.com/1/vod/thumbnail/1jhvl2uqg6xjc.jpg',
                'duration': 8012,
            },
        },
        # mp4 test
        {
            'url': 'https://player.vod2.infomaniak.com/embed/1jhvl2uq7kr4y',
            'md5': 'd06fb3fc5a8d7cb4d6e4a0f4e7c5a76a',
            'info_dict': {
                'id': '1jhvl2uq7kr4y',
                'ext': 'mp4',
                'title': 'RolandCarey2016-05-04.mp4',
                'thumbnail': 'https://res.vod2.infomaniak.com/1/vod/thumbnail/1jhvl2uq8yqqv.jpg',
                'duration': 221,
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # no useful data in given url, formatted url below reveals json data
        data_url = 'https://res.vod2.infomaniak.com/{0}/vod/share/{1}'.format(video_id[0], video_id)
        webpage = self._download_json(data_url, video_id)['data']['media'][0]

        url = webpage['source']['url']
        title = webpage['title']
        thumbnail = traverse_obj(webpage, ('image', 'url'), expected_type=url_or_none)
        duration = traverse_obj(webpage, 'duration', expected_type=int_or_none)

        video_mimetype = traverse_obj(webpage, ('source', 'mimetype'), expected_type=lambda x: x.strip() or None)

        info_dict = {
            'id': video_id,
            'url': url,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
        }

        # if file is m3u8
        if video_mimetype == 'application/x-mpegurl':
            info_dict['formats'] = self._extract_m3u8_formats(
                info_dict.pop('url'), video_id, ext='m3u8', entry_protocol='m3u8_native', m3u8_id='hls')
            self._sort_formats(info_dict['formats'])

        return info_dict
