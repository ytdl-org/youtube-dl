# coding: utf-8
from __future__ import unicode_literals

import time

from .common import InfoExtractor
from ..utils import (
    encode_dict,
    remove_end,
    urlencode_postdata,
)
from ..compat import compat_urllib_request


class VidtoIE(InfoExtractor):
    IE_NAME = 'vidto'
    IE_DESC = 'VidTo.me'
    _VALID_URL = r'https?://(?:www\.)?vidto\.me/(?P<id>[0-9a-zA-Z]+)\.html'
    _TEST = {
        'url': 'http://vidto.me/ku5glz52nqe1.html',
        'info_dict': {
            'id': 'ku5glz52nqe1',
            'ext': 'mp4',
            'title': 'test'
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        page = self._download_webpage(
            'http://vidto.me/%s.html' % video_id, video_id, 'Downloading video page')

        title = remove_end(self._html_search_regex(
            r'<Title>\s*([^<]+)\s*</Title>', page, 'title'), ' - Vidto')

        hidden_fields = self._hidden_inputs(page)

        self.to_screen('Waiting for countdown...')
        time.sleep(7)

        req = compat_urllib_request.Request(
            url, urlencode_postdata(encode_dict(hidden_fields)))
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        post_result = self._download_webpage(
            req, video_id,
            note='Proceed to video...', errnote='unable to proceed')

        file_link = self._search_regex(
            r'file_link\s*=\s*\'(https?:\/\/[0-9a-zA-z.\/\-_]+)', post_result, 'file_link')

        return {
            'id': video_id,
            'url': file_link,
            'title': title,
        }
