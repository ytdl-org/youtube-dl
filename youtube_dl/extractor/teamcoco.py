import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class TeamcocoIE(InfoExtractor):
    _VALID_URL = r'http://teamcoco\.com/video/(?P<url_title>.*)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        url_title = mobj.group('url_title')
        webpage = self._download_webpage(url, url_title)

        video_id = self._html_search_regex(r'<article class="video" data-id="(\d+?)"',
            webpage, u'video id')

        self.report_extraction(video_id)

        video_title = self._html_search_regex(r'<meta property="og:title" content="(.+?)"',
            webpage, u'title')

        thumbnail = self._html_search_regex(r'<meta property="og:image" content="(.+?)"',
            webpage, u'thumbnail', fatal=False)

        video_description = self._html_search_regex(r'<meta property="og:description" content="(.*?)"',
            webpage, u'description', fatal=False)

        data_url = 'http://teamcoco.com/cvp/2.0/%s.xml' % video_id
        data = self._download_webpage(data_url, video_id, 'Downloading data webpage')

        video_url = self._html_search_regex(r'<file type="high".*?>(.*?)</file>',
            data, u'video URL')

        return [{
            'id':          video_id,
            'url':         video_url,
            'ext':         'mp4',
            'title':       video_title,
            'thumbnail':   thumbnail,
            'description': video_description,
        }]
