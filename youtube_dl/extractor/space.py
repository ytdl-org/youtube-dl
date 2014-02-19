from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .brightcove import BrightcoveIE
from ..utils import RegexNotFoundError, ExtractorError


class SpaceIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?space\.com/\d+-(?P<title>[^/\.\?]*?)-video\.html'
    _TEST = {
        'add_ie': ['Brightcove'],
        'url': 'http://www.space.com/23373-huge-martian-landforms-detail-revealed-by-european-probe-video.html',
        'info_dict': {
            'id': '2780937028001',
            'ext': 'mp4',
            'title': 'Huge Martian Landforms\' Detail Revealed By European Probe | Video',
            'description': 'md5:db81cf7f3122f95ed234b631a6ea1e61',
            'uploader': 'TechMedia Networks',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        title = mobj.group('title')
        webpage = self._download_webpage(url, title)
        try:
            # Some videos require the playerKey field, which isn't define in
            # the BrightcoveExperience object
            brightcove_url = self._og_search_video_url(webpage)
        except RegexNotFoundError:
            # Other videos works fine with the info from the object
            brightcove_url = BrightcoveIE._extract_brightcove_url(webpage)
        if brightcove_url is None:
            raise ExtractorError(u'The webpage does not contain a video', expected=True)
        return self.url_result(brightcove_url, BrightcoveIE.ie_key())
