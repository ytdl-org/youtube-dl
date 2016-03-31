# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import (
    ExtractorError,
    sanitized_Request,
    urlencode_postdata,
)


class Vbox7IE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vbox7\.com/play:(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://vbox7.com/play:249bb972c2',
        'md5': '99f65c0c9ef9b682b97313e052734c3f',
        'info_dict': {
            'id': '249bb972c2',
            'ext': 'mp4',
            'title': 'Смях! Чудо - чист за секунди - Скрита камера',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        # need to get the page 3 times for the correct jsSecretToken cookie
        # which is necessary for the correct title
        def get_session_id():
            redirect_page = self._download_webpage(url, video_id)
            session_id_url = self._search_regex(
                r'var\s*url\s*=\s*\'([^\']+)\';', redirect_page,
                'session id url')
            self._download_webpage(
                compat_urlparse.urljoin(url, session_id_url), video_id,
                'Getting session id')

        get_session_id()
        get_session_id()

        webpage = self._download_webpage(url, video_id,
                                         'Downloading redirect page')

        title = self._html_search_regex(r'<title>(.*)</title>',
                                        webpage, 'title').split('/')[0].strip()

        info_url = 'http://vbox7.com/play/magare.do'
        data = urlencode_postdata({'as3': '1', 'vid': video_id})
        info_request = sanitized_Request(info_url, data)
        info_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        info_response = self._download_webpage(info_request, video_id, 'Downloading info webpage')
        if info_response is None:
            raise ExtractorError('Unable to extract the media url')
        (final_url, thumbnail_url) = map(lambda x: x.split('=')[1], info_response.split('&'))

        return {
            'id': video_id,
            'url': final_url,
            'title': title,
            'thumbnail': thumbnail_url,
        }
