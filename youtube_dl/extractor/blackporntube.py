# coding: utf-8
from __future__ import unicode_literals

from .vxxx import VXXXIE


class BlackPornTubeIE(VXXXIE):
    _VALID_URL = r'https?://blackporn\.tube/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://blackporn.tube/video/10043813/young-ebony-babe-gets-super-wet/',
        'md5': '4a4c126970f2f1453b8b2050947fc870',
        'info_dict': {
            'id': '10043813',
            'ext': 'mp4',
            'title': 'Young Ebony Babe Gets Super Wet',
            'display_id': 'young-ebony-babe-gets-super-wet',
            'thumbnail': 'https://tn.blackporn.tube/contents/videos_screenshots/10043000/10043813/480x270/1.jpg',
            'description': '',
            'timestamp': 1654806141,
            'upload_date': '20220609',
            'duration': 193.0,
            'categories': ['BDSM', 'Bondage', 'Celebrity', 'Ebony', 'Fetish',
                           'Shibari Bondage', 'Solo Female',
                           'Tattoo'],
            'age_limit': 18,
        }
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            'https://blackporn.tube/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://blackporn.tube'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://blackporn.tube/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://blackporn.tube'}
        )

    def _get_video_host(self):
        return 'blackporn.tube'
