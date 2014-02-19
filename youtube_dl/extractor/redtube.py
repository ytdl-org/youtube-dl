from __future__ import unicode_literals

import re

from .common import InfoExtractor


class RedTubeIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?redtube\.com/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.redtube.com/66418',
        'file': '66418.mp4',
        # md5 varies from time to time, as in
        # https://travis-ci.org/rg3/youtube-dl/jobs/14052463#L295
        #'md5': u'7b8c22b5e7098a3e1c09709df1126d2d',
        'info_dict': {
            "title": "Sucked on a toilet",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        video_extension = 'mp4'
        webpage = self._download_webpage(url, video_id)

        self.report_extraction(video_id)

        video_url = self._html_search_regex(
            r'<source src="(.+?)" type="video/mp4">', webpage, u'video URL')

        video_title = self._html_search_regex(
            r'<h1 class="videoTitle[^"]*">(.+?)</h1>',
            webpage, u'title')

        video_thumbnail = self._html_search_regex(
            r'playerInnerHTML.+?<img\s+src="(.+?)"',
            webpage, u'thumbnail', fatal=False)

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return {
            'id': video_id,
            'url': video_url,
            'ext': video_extension,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'age_limit': age_limit,
        }
