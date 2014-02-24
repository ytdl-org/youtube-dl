from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urlparse
)


class NovaMovIE(InfoExtractor):
    IE_NAME = 'novamov'
    IE_DESC = 'NovaMov'

    _VALID_URL = r'http://(?:(?:www\.)?%(host)s/video/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<videoid>[a-z\d]{13})' % {'host': 'novamov\.com'}

    _HOST = 'www.novamov.com'

    _FILE_DELETED_REGEX = r'This file no longer exists on our servers!</h2>'
    _FILEKEY_REGEX = r'flashvars\.filekey="(?P<filekey>[^"]+)";'
    _TITLE_REGEX = r'(?s)<div class="v_tab blockborder rounded5" id="v_tab1">\s*<h3>([^<]+)</h3>'
    _DESCRIPTION_REGEX = r'(?s)<div class="v_tab blockborder rounded5" id="v_tab1">\s*<h3>[^<]+</h3><p>([^<]+)</p>'

    _TEST = {
        'url': 'http://www.novamov.com/video/4rurhn9x446jj',
        'md5': '7205f346a52bbeba427603ba10d4b935',
        'info_dict': {
            'id': '4rurhn9x446jj',
            'ext': 'flv',
            'title': 'search engine optimization',
            'description': 'search engine optimization is used to rank the web page in the google search engine'
        },
        'skip': '"Invalid token" errors abound (in web interface as well as youtube-dl, there is nothing we can do about it.)'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        page = self._download_webpage(
            'http://%s/video/%s' % (self._HOST, video_id), video_id, 'Downloading video page')

        if re.search(self._FILE_DELETED_REGEX, page) is not None:
            raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)

        filekey = self._search_regex(self._FILEKEY_REGEX, page, 'filekey')

        title = self._html_search_regex(self._TITLE_REGEX, page, 'title', fatal=False)

        description = self._html_search_regex(self._DESCRIPTION_REGEX, page, 'description', default='', fatal=False)

        api_response = self._download_webpage(
            'http://%s/api/player.api.php?key=%s&file=%s' % (self._HOST, filekey, video_id), video_id,
            'Downloading video api response')

        response = compat_urlparse.parse_qs(api_response)

        if 'error_msg' in response:
            raise ExtractorError('%s returned error: %s' % (self.IE_NAME, response['error_msg'][0]), expected=True)

        video_url = response['url'][0]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description
        }