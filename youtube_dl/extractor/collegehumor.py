import json
import re

from .common import InfoExtractor


class CollegeHumorIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?collegehumor\.com/(video|embed|e)/(?P<videoid>[0-9]+)/?(?P<shorttitle>.*)$'

    _TESTS = [{
        u'url': u'http://www.collegehumor.com/video/6902724/comic-con-cosplay-catastrophe',
        u'file': u'6902724.mp4',
        u'md5': u'dcc0f5c1c8be98dc33889a191f4c26bd',
        u'info_dict': {
            u'title': u'Comic-Con Cosplay Catastrophe',
            u'description': u'Fans get creative this year at San Diego.  Too',
            u'age_limit': 13,
        },
    },
    {
        u'url': u'http://www.collegehumor.com/video/3505939/font-conference',
        u'file': u'3505939.mp4',
        u'md5': u'72fa701d8ef38664a4dbb9e2ab721816',
        u'info_dict': {
            u'title': u'Font Conference',
            u'description': u'This video wasn\'t long enough, so we made it double-spaced.',
            u'age_limit': 10,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        jsonUrl = 'http://www.collegehumor.com/moogaloop/video/' + video_id + '.json'
        data = json.loads(self._download_webpage(
            jsonUrl, video_id, u'Downloading info JSON'))
        vdata = data['video']

        AGE_LIMITS = {'nc17': 18, 'r': 18, 'pg13': 13, 'pg': 10, 'g': 0}
        rating = vdata.get('rating')
        if rating:
            age_limit = AGE_LIMITS.get(rating.lower())
        else:
            age_limit = None  # None = No idea

        PREFS = {'high_quality': 2, 'low_quality': 0}
        formats = []
        for format_key in ('mp4', 'webm'):
            for qname, qurl in vdata[format_key].items():
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
