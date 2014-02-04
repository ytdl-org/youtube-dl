from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor


class CollegeHumorIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/(video|embed|e)/(?P<videoid>[0-9]+)/?(?P<shorttitle>.*)$'

    _TESTS = [{
        'url': 'http://www.collegehumor.com/video/6902724/comic-con-cosplay-catastrophe',
        'file': '6902724.mp4',
        'md5': 'dcc0f5c1c8be98dc33889a191f4c26bd',
        'info_dict': {
            'title': 'Comic-Con Cosplay Catastrophe',
            'description': 'Fans get creative this year at San Diego.  Too',
            'age_limit': 13,
        },
    },
    {
        'url': 'http://www.collegehumor.com/video/3505939/font-conference',
        'file': '3505939.mp4',
        'md5': '72fa701d8ef38664a4dbb9e2ab721816',
        'info_dict': {
            'title': 'Font Conference',
            'description': 'This video wasn\'t long enough, so we made it double-spaced.',
            'age_limit': 10,
        },
    },
    # embedded youtube video
    {
        'url': 'http://www.collegehumor.com/embed/6950457',
        'info_dict': {
            'id': 'W5gMp3ZjYg4',
            'ext': 'mp4',
            'title': 'Funny Dogs Protecting Babies Compilation 2014 [NEW HD]',
            'uploader': 'Funnyplox TV',
            'uploader_id': 'funnyploxtv',
            'description': 'md5:11812366244110c3523968aa74f02521',
            'upload_date': '20140128',
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

        return {
            'id': video_id,
            'title': vdata['title'],
            'description': vdata.get('description'),
            'thumbnail': vdata.get('thumbnail'),
            'formats': formats,
            'age_limit': age_limit,
        }
