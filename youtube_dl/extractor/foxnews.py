from __future__ import unicode_literals

import re

from .amp import AMPIE
from .common import InfoExtractor


class FoxNewsIE(AMPIE):
    IE_DESC = 'Fox News and Fox Business Video'
    _VALID_URL = r'https?://(?P<host>video\.(?:insider\.)?fox(?:news|business)\.com)/v/(?:video-embed\.html\?video_id=)?(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://video.foxnews.com/v/3937480/frozen-in-time/#sp=show-clips',
            'md5': '32aaded6ba3ef0d1c04e238d01031e5e',
            'info_dict': {
                'id': '3937480',
                'ext': 'flv',
                'title': 'Frozen in Time',
                'description': '16-year-old girl is size of toddler',
                'duration': 265,
                'timestamp': 1304411491,
                'upload_date': '20110503',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'http://video.foxnews.com/v/3922535568001/rep-luis-gutierrez-on-if-obamas-immigration-plan-is-legal/#sp=show-clips',
            'md5': '5846c64a1ea05ec78175421b8323e2df',
            'info_dict': {
                'id': '3922535568001',
                'ext': 'mp4',
                'title': "Rep. Luis Gutierrez on if Obama's immigration plan is legal",
                'description': "Congressman discusses president's plan",
                'duration': 292,
                'timestamp': 1417662047,
                'upload_date': '20141204',
                'thumbnail': 're:^https?://.*\.jpg$',
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://video.foxnews.com/v/video-embed.html?video_id=3937480&d=video.foxnews.com',
            'only_matching': True,
        },
        {
            'url': 'http://video.foxbusiness.com/v/4442309889001',
            'only_matching': True,
        },
        {
            # From http://insider.foxnews.com/2016/08/25/univ-wisconsin-student-group-pushing-silence-certain-words
            'url': 'http://video.insider.foxnews.com/v/video-embed.html?video_id=5099377331001&autoplay=true&share_url=http://insider.foxnews.com/2016/08/25/univ-wisconsin-student-group-pushing-silence-certain-words&share_title=Student%20Group:%20Saying%20%27Politically%20Correct,%27%20%27Trash%27%20and%20%27Lame%27%20Is%20Offensive&share=true',
            'only_matching': True,
        },
    ]

    def _real_extract(self, url):
        host, video_id = re.match(self._VALID_URL, url).groups()

        info = self._extract_feed_info(
            'http://%s/v/feed/video/%s.js?template=fox' % (host, video_id))
        info['id'] = video_id
        return info


class FoxNewsInsiderIE(InfoExtractor):
    _VALID_URL = r'https?://insider\.foxnews\.com/([^/]+/)+(?P<id>[a-z-]+)'
    IE_NAME = 'foxnews:insider'

    _TEST = {
        'url': 'http://insider.foxnews.com/2016/08/25/univ-wisconsin-student-group-pushing-silence-certain-words',
        'md5': 'a10c755e582d28120c62749b4feb4c0c',
        'info_dict': {
            'id': '5099377331001',
            'display_id': 'univ-wisconsin-student-group-pushing-silence-certain-words',
            'ext': 'mp4',
            'title': 'Student Group: Saying \'Politically Correct,\' \'Trash\' and \'Lame\' Is Offensive',
            'description': 'Is campus censorship getting out of control?',
            'timestamp': 1472168725,
            'upload_date': '20160825',
            'thumbnail': 're:^https?://.*\.jpg$',
        },
        'add_ie': [FoxNewsIE.ie_key()],
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        embed_url = self._html_search_meta('embedUrl', webpage, 'embed URL')

        title = self._og_search_title(webpage)
        description = self._og_search_description(webpage)

        return {
            '_type': 'url_transparent',
            'ie_key': FoxNewsIE.ie_key(),
            'url': embed_url,
            'display_id': display_id,
            'title': title,
            'description': description,
        }
