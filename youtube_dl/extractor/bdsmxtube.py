# coding: utf-8
from __future__ import unicode_literals

from .vxxx import VXXXIE


class BdsmxTubeIE(VXXXIE):
    _VALID_URL = r'https?://bdsmx\.tube/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://bdsmx.tube/video/127583/latex-puppy-leashed/',
        'md5': '06b6000c19207cb068bc0009f243345d',
        'info_dict': {
            'id': '127583',
            'ext': 'mp4',
            'title': 'Latex Puppy Leashed',
            'display_id': 'latex-puppy-leashed',
            'thumbnail': 'https://tn.bdsmx-porn.com/contents/videos_screenshots/127000/127583/480x270/1.jpg',
            'description': '',
            'timestamp': 1651003323,
            'upload_date': '20220426',
            'duration': 68.0,
            'categories': ['Asian', 'Brunette', 'Cosplay', 'Fetish',
                           'Fuck Machine', 'Gagging', 'Japanese',
                           'JAV Uncensored', 'Latex', 'Leather', 'POV'],
            'age_limit': 18,
        }
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            'https://bdsmx.tube/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://bdsmx.tube'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://bdsmx.tube/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://bdsmx.tube'}
        )

    def _get_video_host(self):
        return 'bdsmx.tube'
