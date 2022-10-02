# coding: utf-8
from __future__ import unicode_literals

from .vxxx import VXXXIE


class InPornIE(VXXXIE):
    _VALID_URL = r'https?://(?:www\.)?inporn\.com/video/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://inporn.com/video/533613/2k-t-2nd-season-parm-151/',
        'md5': '111e5c4680b1fa5995144e101c521a4f',
        'info_dict': {
            'id': '533613',
            'ext': 'mp4',
            'title': '2k 美月まい - ガーリー系アパレルモt゙ルの挑発パンチラ 2nd Season [parm-151]',
            'display_id': '2k-t-2nd-season-parm-151',
            'thumbnail': 'https://tn.inporn.com/media/tn/533613_1.jpg',
            'description': '',
            'timestamp': 1664571262,
            'upload_date': '20220930',
            'duration': 480.0,
            'categories': ['Asian', 'Brunette', 'Casting', 'HD', 'Japanese',
                           'JAV Uncensored'],
            'age_limit': 18,
        },
    }]

    def _download_info_object(self, video_id):
        return self._download_json(
            'https://inporn.com/api/json/video/86400/0/{}/{}.json'.format(
                int(video_id) // 1000 * 1000,
                video_id,
            ), video_id, headers={'Referer': 'https://inporn.com'})['video']

    def _download_format_object(self, video_id):
        return self._download_json(
            'https://inporn.com/api/videofile.php?video_id={}'.format(video_id),
            video_id,
            headers={'Referer': 'https://inporn.com'}
        )

    def _get_video_host(self):
        return 'inporn.com'
