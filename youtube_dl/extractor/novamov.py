from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
)


class NovaMovIE(InfoExtractor):
    IE_NAME = 'novamov'
    IE_DESC = 'NovaMov'

    _VALID_URL_TEMPLATE = r'http://(?:(?:www\.)?%(host)s/(?:file|video)/|(?:(?:embed|www)\.)%(host)s/embed\.php\?(?:.*?&)?v=)(?P<id>[a-z\d]{13})'
    _VALID_URL = _VALID_URL_TEMPLATE % {'host': 'novamov\.com'}

    _HOST = 'www.novamov.com'

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

        video_data = self._download_json(
            'http://%s/mobile/ajax.php?videoId=%s' % (self._HOST, video_id),
            video_id, 'Downloading video page')

        if video_data.get('error'):
            raise ExtractorError(
                '%s said: The video does not exist or has been deleted.' % self.IE_NAME,
                expected=True)

        video_data = video_data['items'][0]

        request = HEADRequest('http://%s/mobile/%s' % (self._HOST, video_data['download']))
        # resolve the url so that we can detect the correct extension
        head = self._request_webpage(request, video_id)
        video_url = head.geturl()

        return {
            'id': video_id,
            'url': video_url,
            'title': video_data['title'],
            'description': video_data.get('desc'),
        }
