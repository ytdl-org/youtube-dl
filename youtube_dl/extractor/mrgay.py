# coding: utf-8
from __future__ import unicode_literals

from .vxxx import VXXXIE


class MrGayIE(VXXXIE):
    _VALID_URL = r'https?://mrgay\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://mrgay.com/video/10169199/jpn-crossdresser-6/',
        'md5': 'b5780a9437c205b4bc87eb939b23e8ef',
        'info_dict': {
            'id': '10169199',
            'ext': 'mp4',
            'title': 'Jpn Crossdresser 6',
            'display_id': 'jpn-crossdresser-6',
            'thumbnail': 'https://tn.mrgay.com/media/tn/10169199_1.jpg',
            'description': '',
            'timestamp': 1651066888,
            'upload_date': '20220427',
            'duration': 834.0,
            'categories': ['Amateur', 'Asian', 'Brunette', 'Crossdressing',
                           'Japanese', 'Webcam'],
            'age_limit': 18,
        }
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            'https://mrgay.com/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://mrgay.com'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://mrgay.com/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://mrgay.com'}
        )

    def _get_video_host(self):
        return 'mrgay.com'
