from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import encode_dict
from ..compat import (
    compat_urllib_request,
    compat_urllib_parse,
    compat_urlparse
)
from ..utils import (
    ExtractorError,
)
import re

class NowVideoIE(InfoExtractor):
    IE_NAME = 'nowvideo'
    IE_DESC = 'NowVideo'

    _VALID_URL = r'http://(?:(?:www\.)?%(host)s/(?:file|video)/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<id>[a-z\d]{13})' % {'host': 'nowvideo\.(?:ch|ec|sx|eu|at|ag|co|li)'}

    _HOST = 'www.nowvideo.li'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _FILEKEY_REGEX = r'var fkzd="([^"]+)";'
    _STEPKEY_REGEX = r'<input type="hidden" name="stepkey" value="(.+)">'

    _TEST = {
        'url': 'http://www.nowvideo.li/video/edb2ded3aa118',
        'info_dict': {
            'id': 'edb2ded3aa118',
            'ext': 'mp4',
            'title': 'test'
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        page = self._download_webpage(url, video_id, 'Downloading video page')

        if re.search(self._FILE_DELETED_REGEX, page) is not None:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        stepkey_value = self._search_regex(self._STEPKEY_REGEX, page, 'stepkey', fatal=True)

        form_str = {
            'stepkey': stepkey_value,
        }
        post_data = compat_urllib_parse.urlencode(encode_dict(form_str)).encode('ascii')
        req = compat_urllib_request.Request(url, post_data)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        post_result = self._download_webpage(
            req, video_id,
            note='Proceed to video...', errnote='unable to proceed', fatal=True)

        filekey = self._search_regex(self._FILEKEY_REGEX, post_result, 'token', fatal=True)

        api_response = self._download_webpage(
            'http://%s/api/player.api.php?key=%s&file=%s' % (self._HOST, filekey, video_id), video_id,
            'Downloading video api response')

        response = compat_urlparse.parse_qs(api_response)

        if 'error_msg' in response:
            raise ExtractorError('%s returned error: %s' % (self.IE_NAME, response['error_msg'][0]), expected=True)

        video_url = response['url'][0]
        title = response['title'][0]

        return {
            'id': video_id,
            'url': video_url,
            'title': title
        }
