# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor


class NateIE(InfoExtractor):
    _VALID_URL = r'https?://(?:m\.)?tv\.nate\.com/clip/(?P<id>[0-9]+)'
    _API_BASE_TMPL = 'https://tv.nate.com/api/v1/clip/%s'
    _TEST = {
        'url': 'https://tv.nate.com/clip/4300566',
        #'md5': '02D3CAB3907B60C58043761F8B5BF2B3',
        'info_dict': {
            'id': '4300566',
            'ext': 'mp4',
            'title': '[심쿵엔딩] 이준호x이세영, 서로를 기억하며 끌어안는 두 사람!💕, MBC 211204 방송',
            'thumbnail': r're:^http?://.*\.jpg$',
            'upload_date': '20211204',
            'age_limit' : 15
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        #video_data = self._download_json(
        #    'https://tv.nate.com/api/v1/clip/% s'%video_id, video_id, headers=self.geo_verification_headers())
        video_data = self._download_json('https://tv.nate.com/api/v1/clip/' + str(video_id), video_id)

        title = video_data.get('clipTitle')
        thumbnail = video_data.get('contentImg')
        upload_date = video_data.get('regDate')
        age_limit = video_data.get('targetAge')
        url = video_data['smcUriList'][4]

        # TODO more code goes here, for example ...

        return {
            'id': video_id,
            'title': title,
            'thumbnail' : thumbnail,
            'upload_date' : upload_date[:8],
            'age_limit' : age_limit,
            'url': url
            # TODO more properties (see youtube_dl/extractor/common.py)
        }
