from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import int_or_none


class CollegeHumorIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/(video|embed|e)/(?P<videoid>[0-9]+)/?(?P<shorttitle>.*)$'

    _TESTS = [{
        'url': 'http://www.collegehumor.com/video/6902724/comic-con-cosplay-catastrophe',
        'md5': 'dcc0f5c1c8be98dc33889a191f4c26bd',
        'info_dict': {
            'id': '6902724',
            'ext': 'mp4',
            'title': 'Comic-Con Cosplay Catastrophe',
            'description': "Fans get creative this year at San Diego.  Too creative.  And yes, that's really Joss Whedon.",
            'age_limit': 13,
            'duration': 187,
        },
    },
    {
        'url': 'http://www.collegehumor.com/video/3505939/font-conference',
        'md5': '72fa701d8ef38664a4dbb9e2ab721816',
        'info_dict': {
            'id': '3505939',
            'ext': 'mp4',
            'title': 'Font Conference',
            'description': "This video wasn't long enough, so we made it double-spaced.",
            'age_limit': 10,
            'duration': 179,
        },
    },
    # embedded youtube video
    {
        'url': 'http://www.collegehumor.com/embed/6950306',
        'info_dict': {
            'id': 'Z-bao9fg6Yc',
            'ext': 'mp4',
            'title': 'Young Americans Think President John F. Kennedy Died THIS MORNING IN A CAR ACCIDENT!!!',
            'uploader': 'Mark Dice',
            'uploader_id': 'MarkDice',
            'description': 'md5:62c3dab9351fac7bb44b53b69511d87f',
            'upload_date': '20140127',
        },
        'params': {
            'skip_download': True,
        },
        'add_ie': ['Youtube'],
    },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        jsonUrl = 'http://www.collegehumor.com/moogaloop/video/' + video_id + '.json'
        data = json.loads(self._download_webpage(
            jsonUrl, video_id, 'Downloading info JSON'))
        vdata = data['video']
        if vdata.get('youtubeId') is not None:
            return {
                '_type': 'url',
                'url': vdata['youtubeId'],
                'ie_key': 'Youtube',
            }

        AGE_LIMITS = {'nc17': 18, 'r': 18, 'pg13': 13, 'pg': 10, 'g': 0}
        rating = vdata.get('rating')
        if rating:
            age_limit = AGE_LIMITS.get(rating.lower())
        else:
            age_limit = None  # None = No idea

        PREFS = {'high_quality': 2, 'low_quality': 0}
        formats = []
        for format_key in ('mp4', 'webm'):
            for qname, qurl in vdata.get(format_key, {}).items():
                formats.append({
                    'format_id': format_key + '_' + qname,
                    'url': qurl,
                    'format': format_key,
                    'preference': PREFS.get(qname),
                })
        self._sort_formats(formats)

        duration = int_or_none(vdata.get('duration'), 1000)
        like_count = int_or_none(vdata.get('likes'))

        return {
            'id': video_id,
            'title': vdata['title'],
            'description': vdata.get('description'),
            'thumbnail': vdata.get('thumbnail'),
            'formats': formats,
            'age_limit': age_limit,
            'duration': duration,
            'like_count': like_count,
        }
