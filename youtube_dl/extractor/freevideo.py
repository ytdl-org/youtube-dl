from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class FreeVideoIE(InfoExtractor):
    _VALID_URL = r'^http://www.freevideo.cz/vase-videa/(?P<videoid>[^.]+)\.html$'

    _TEST = {
        'url': 'http://www.freevideo.cz/vase-videa/vysukany-zadecek-22033.html',
        'file': 'vysukany-zadecek-22033.mp4',
        'info_dict': {
            "title": "vysukany-zadecek-22033",
            "age_limit": 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % query)

        video_id = mobj.group('videoid')

        # Get webpage content
        webpage = self._download_webpage(url, video_id)

        age_limit = self._rta_search(webpage)
        if age_limit == 0:
            # interpret 0 as mis-detection since this site is adult-content only.
            # However, if we get non-0, assume the rtalabel started giving proper
            # results
            age_limit = 18

        url = re.search(r'\s+url: "(http://[a-z0-9-]+.cdn.freevideo.cz/stream/.*/video.mp4)"', webpage)
        if url is None:
            raise ExtractorError('ERROR: unable to extract video url')

        return {
            'id': video_id,
            'url': url.groups()[0],
            'title': video_id,
            'age_limit': age_limit,
        }
