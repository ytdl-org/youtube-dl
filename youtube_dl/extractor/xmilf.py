# coding: utf-8
from __future__ import unicode_literals

from .vxxx import VXXXIE


class XMilfIE(VXXXIE):
    _VALID_URL = r'https?://xmilf\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://xmilf.com/video/143777/big-boob-brunette-masturbates3/',
        'md5': 'a196fe8daebe194a758754c81e9232ad',
        'info_dict': {
            'id': '143777',
            'ext': 'mp4',
            'title': 'Big Boob Brunette Masturbates',
            'display_id': 'big-boob-brunette-masturbates3',
            'thumbnail': 'https://tn.xmilf.com/contents/videos_screenshots/143000/143777/480x270/1.jpg',
            'description': '',
            'timestamp': 1662465481,
            'upload_date': '20220906',
            'duration': 480.0,
            'categories': ['Amateur', 'Big Tits', 'Brunette', 'Fetish', 'HD',
                           'Lingerie', 'MILF', 'Webcam'],
            'age_limit': 18,
        }
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            'https://xmilf.com/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://xmilf.com'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://xmilf.com/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://xmilf.com'}
        )

    def _get_video_host(self):
        return 'xmilf.com'
