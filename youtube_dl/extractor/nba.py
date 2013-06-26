import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
)


class NBAIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:watch\.|www\.)?nba\.com/(?:nba/)?video(/[^?]*?)(?:/index\.html)?(?:\?.*)?$'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)

        video_id = mobj.group(1)

        webpage = self._download_webpage(url, video_id)

        video_url = u'http://ht-mobile.cdn.turner.com/nba/big' + video_id + '_nba_1280x720.mp4'

        shortened_video_id = video_id.rpartition('/')[2]
        title = self._html_search_regex(r'<meta property="og:title" content="(.*?)"',
            webpage, 'title', default=shortened_video_id).replace('NBA.com: ', '')

        # It isn't there in the HTML it returns to us
        # uploader_date = self._html_search_regex(r'<b>Date:</b> (.*?)</div>', webpage, 'upload_date', fatal=False)

        description = self._html_search_regex(r'<meta name="description" (?:content|value)="(.*?)" />', webpage, 'description', fatal=False)

        info = {
            'id': shortened_video_id,
            'url': video_url,
            'ext': 'mp4',
            'title': title,
            # 'uploader_date': uploader_date,
            'description': description,
        }
        return [info]
