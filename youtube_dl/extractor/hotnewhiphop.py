from __future__ import unicode_literals

import re
import base64

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,
    ExtractorError,
    HEADRequest,
)


class HotNewHipHopIE(InfoExtractor):
    _VALID_URL = r'http://www\.hotnewhiphop\.com/.*\.(?P<id>.*)\.html'
    _TEST = {
        'url': 'http://www.hotnewhiphop.com/freddie-gibbs-lay-it-down-song.1435540.html',
        'file': '1435540.mp3',
        'md5': '2c2cd2f76ef11a9b3b581e8b232f3d96',
        'info_dict': {
            'title': 'Freddie Gibbs - Lay It Down'
        }
    }

    def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        video_id = m.group('id')

        webpage_src = self._download_webpage(url, video_id)

        video_url_base64 = self._search_regex(
            r'data-path="(.*?)"', webpage_src, u'video URL', fatal=False)

        if video_url_base64 is None:
            video_url = self._search_regex(
                r'"contentUrl" content="(.*?)"', webpage_src, u'video URL')
            return self.url_result(video_url, ie='Youtube')

        reqdata = compat_urllib_parse.urlencode([
            ('mediaType', 's'),
            ('mediaId', video_id),
        ])
        r = compat_urllib_request.Request(
            'http://www.hotnewhiphop.com/ajax/media/getActions/', data=reqdata)
        r.add_header('Content-Type', 'application/x-www-form-urlencoded')
        mkd = self._download_json(
            r, video_id, note='Requesting media key',
            errnote='Could not download media key')
        if 'mediaKey' not in mkd:
            raise ExtractorError('Did not get a media key')

        redirect_url = base64.b64decode(video_url_base64).decode('utf-8')
        redirect_req = HEADRequest(redirect_url)
        req = self._request_webpage(
            redirect_req, video_id,
            note='Resolving final URL', errnote='Could not resolve final URL')
        video_url = req.geturl()
        if video_url.endswith('.html'):
            raise ExtractorError('Redirect failed')

        video_title = self._og_search_title(webpage_src).strip()

        return {
            'id': video_id,
            'url': video_url,
            'title': video_title,
            'thumbnail': self._og_search_thumbnail(webpage_src),
        }
