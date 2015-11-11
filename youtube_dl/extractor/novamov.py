from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urlparse,
)
from ..utils import (
    ExtractorError,
    NO_DEFAULT,
    encode_dict,
    urlencode_postdata,
)


class NovaMovIE(InfoExtractor):
    IE_NAME = 'novamov'
    IE_DESC = 'NovaMov'

    _VALID_URL_TEMPLATE = r'http://(?:(?:www\.)?%(host)s/(?:file|video)/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<id>[a-z\d]{13})'
    _VALID_URL = _VALID_URL_TEMPLATE % {'host': 'novamov\.com'}

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
        video_id = self._match_id(url)

        url = 'http://%s/video/%s' % (self._HOST, video_id)

        webpage = self._download_webpage(
            url, video_id, 'Downloading video page')

        if re.search(self._FILE_DELETED_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        def extract_filekey(default=NO_DEFAULT):
            return self._search_regex(
                self._FILEKEY_REGEX, webpage, 'filekey', default=default)

        filekey = extract_filekey(default=None)

        if not filekey:
            fields = self._hidden_inputs(webpage)
            post_url = self._search_regex(
                r'<form[^>]+action=(["\'])(?P<url>.+?)\1', webpage,
                'post url', default=url, group='url')
            if not post_url.startswith('http'):
                post_url = compat_urlparse.urljoin(url, post_url)
            request = compat_urllib_request.Request(
                post_url, urlencode_postdata(encode_dict(fields)))
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
            request.add_header('Referer', post_url)
            webpage = self._download_webpage(
                request, video_id, 'Downloading continue to the video page')

        filekey = extract_filekey()

        title = self._html_search_regex(self._TITLE_REGEX, webpage, 'title', fatal=False)
        description = self._html_search_regex(self._DESCRIPTION_REGEX, webpage, 'description', default='', fatal=False)

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
