from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urlparse
)


class VideoweedIE(InfoExtractor):
    IE_NAME = 'videoweed'
    IE_DESC = 'VideoWEED'

    #_VALID_URL = r'http://(?:(?:www\.)?%(host)s/file/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<videoid>[a-z\d]{13})' % {'host': 'videoweed\.com'}
    _VALID_URL =r'http://(?:www\.)videoweed\.es/file/(?P<id>[^"]+)'
    _HOST = 'www.videoweed.es'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.</'
    _FILEKEY_REGEX = r'flashvars\.filekey="(?P<filekey>[^"]+)";'
    _TITLE_REGEX = r'<h1 class="text_shadow">([^<]+)</h1>'
    _DESCRIPTION_REGEX = r'(?s)<div class="v_tab blockborder rounded5" id="v_tab1">\s*<h3>[^<]+</h3><p>([^<]+)</p>'

    _TEST = {
        'url': 'http://www.videoweed.es/file/89868b4aa3bdf',
        'md5': '7205f346a52bbeba427603ba10d4b935',
        'info_dict': {
            'id': '89868b4aa3bdf',
            'ext': 'flv',
            'title': 'law and order svu 103 dvdrip',
            'description': ''
        },
        'skip': '"Invalid token" errors abound (in web interface as well as youtube-dl, there is nothing we can do about it.)'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        
        page = self._download_webpage(
            'http://%s/file/%s' % (self._HOST, video_id), video_id, 'Downloading video page')

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