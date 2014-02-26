import re
from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
)

class ProsiebenSat1IE(InfoExtractor):
    """Information Extractor for ProsiebenSat1"""
    _VALID_URL = r'http://(?:www\.)?(?P<url>(?:prosieben|prosiebenmaxx|sixx|sat1|kabeleins|the-voice-of-germany)\.de/([^/]+/)*?videos?/.+)'
    _TESTS = [
        {
            'url': 'http://www.prosieben.de/tv/got-to-dance/video/11-first-look-team-recycled-clip',
            'file': '9160151.flv',
            'params': {
                'skip_download': True,
            }
        }
    ]

    def _real_extract(self,url):
        def unescape(s):
            return s.encode("ascii", "ignore").decode('unicode_escape')

        mobj = re.match(self._VALID_URL, url)

        url = u'http://www.' + mobj.group('url')
        webpage = self._download_webpage(url, None)
        artist = unescape(self._search_regex(r'"show_artist":"([^"]+)', webpage, 'title'))
        title = unescape(self._search_regex(r'"clipList":\[{"title":"([^"]+)', webpage, 'artist'))

        # Encode with utf-8 for python2 compatibility
        search_url = u'http://www.myvideo.de/search?q=%s&category=TV' % compat_urllib_parse.quote_plus((title + u' - ' + artist).encode('utf-8'))
        search_webpage = self._download_webpage(search_url, None, note='Searching video')

        result_url = u'http://www.myvideo.de' + self._search_regex(r'search-video" href="(/watch/[^"]+)', search_webpage, 'result_url')

        return self.url_result(result_url, 'MyVideo')
