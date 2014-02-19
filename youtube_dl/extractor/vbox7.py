# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_parse,
    compat_urllib_request,

    ExtractorError,
)


class Vbox7IE(InfoExtractor):
    _VALID_URL = r'http://(www\.)?vbox7\.com/play:(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://vbox7.com/play:249bb972c2',
        'md5': '99f65c0c9ef9b682b97313e052734c3f',
        'info_dict': {
            'id': '249bb972c2',
            'ext': 'flv',
            'title': 'Смях! Чудо - чист за секунди - Скрита камера',
        },
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        redirect_page, urlh = self._download_webpage_handle(url, video_id)
        new_location = self._search_regex(r'window\.location = \'(.*)\';',
            redirect_page, 'redirect location')
        redirect_url = urlh.geturl() + new_location
        webpage = self._download_webpage(redirect_url, video_id,
            'Downloading redirect page')

        title = self._html_search_regex(r'<title>(.*)</title>',
            webpage, 'title').split('/')[0].strip()

        info_url = "http://vbox7.com/play/magare.do"
        data = compat_urllib_parse.urlencode({'as3': '1', 'vid': video_id})
        info_request = compat_urllib_request.Request(info_url, data)
        info_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        info_response = self._download_webpage(info_request, video_id, 'Downloading info webpage')
        if info_response is None:
            raise ExtractorError('Unable to extract the media url')
        (final_url, thumbnail_url) = map(lambda x: x.split('=')[1], info_response.split('&'))

        return {
            'id': video_id,
            'url': final_url,
            'ext': 'flv',
            'title': title,
            'thumbnail': thumbnail_url,
        }
