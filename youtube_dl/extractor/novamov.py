from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urlparse
)


class NovamovIE(InfoExtractor):
    _VALID_URL = r'http://(?:(?:www\.)?novamov\.com/video/|(?:(?:embed|www)\.)novamov\.com/embed\.php\?v=)(?P<videoid>[a-z\d]{13})'

    _TEST = {
        'url': 'http://www.novamov.com/video/4rurhn9x446jj',
        'file': '4rurhn9x446jj.flv',
        'md5': '7205f346a52bbeba427603ba10d4b935',
        'info_dict': {
            'title': 'search engine optimization',
            'description': 'search engine optimization is used to rank the web page in the google search engine'
        },
        'skip': '"Invalid token" errors abound (in web interface as well as youtube-dl, there is nothing we can do about it.)'
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        page = self._download_webpage('http://www.novamov.com/video/%s' % video_id,
                                      video_id, 'Downloading video page')

        if re.search(r'This file no longer exists on our servers!</h2>', page) is not None:
            raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)

        filekey = self._search_regex(
            r'flashvars\.filekey="(?P<filekey>[^"]+)";', page, 'filekey')

        title = self._html_search_regex(
            r'(?s)<div class="v_tab blockborder rounded5" id="v_tab1">\s*<h3>([^<]+)</h3>',
            page, 'title', fatal=False)

        description = self._html_search_regex(
            r'(?s)<div class="v_tab blockborder rounded5" id="v_tab1">\s*<h3>[^<]+</h3><p>([^<]+)</p>',
            page, 'description', fatal=False)

        api_response = self._download_webpage(
            'http://www.novamov.com/api/player.api.php?key=%s&file=%s' % (filekey, video_id),
            video_id, 'Downloading video api response')

        response = compat_urlparse.parse_qs(api_response)

        if 'error_msg' in response:
            raise ExtractorError('novamov returned error: %s' % response['error_msg'][0], expected=True)

        video_url = response['url'][0]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description
        }
