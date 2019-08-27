# coding: utf-8
from __future__ import unicode_literals

import re

from youtube_dl.utils import HEADRequest, UnsupportedError, unified_strdate
from .common import InfoExtractor
from ..compat import (
    compat_str,
)


class PutIoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?api\.put\.io/v[0-9]+/files/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://app.put.io/files/638463831',
        'only_matching': True,
    }, {
        'url': 'https://api.put.io/v2/files/638474942/download',
        'only_matching': True,
    }, {
        'url': 'https://api.put.io/v2/files/638441619/stream',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self.to_screen('%s: Getting info for file' % video_id)

        head_req = HEADRequest(url)
        head_response = self._request_webpage(head_req, video_id, fatal=True)
        resolved_url = compat_str(head_response.geturl())
        if url == resolved_url:
            # we expect a redirect, so if there is none, this URL is invalid
            raise UnsupportedError(url)

        disposition = head_response.headers.get('Content-Disposition')
        mobj = re.match(r'.*?filename="(?P<title>[^"]+)".*?', disposition)
        title = mobj.group('title') or video_id

        info_dict = {
            'id': video_id,
            'title': title,
            'upload_date': unified_strdate(head_response.headers.get('Last-Modified'))
        }

        # match supported types only, since a URL can point to any type of file
        content_type = head_response.headers.get('Content-Type', '').lower()
        m = re.match(
            r'^(?P<type>audio|video|application(?=/(?:ogg$|(?:vnd\.apple\.|x-)?mpegurl)))/(?P<format_id>[^;\s]+)',
            content_type)
        if m:
            format_id = compat_str(m.group('format_id'))
            if format_id.endswith('mpegurl'):
                formats = self._extract_m3u8_formats(resolved_url, video_id, 'mp4')
            elif format_id == 'f4m':
                formats = self._extract_f4m_formats(resolved_url, video_id)
            else:
                formats = [{
                    'format_id': format_id,
                    'url': resolved_url,
                    'vcodec': 'none' if m.group('type') == 'audio' else None
                }]
                info_dict['direct'] = True
            self._sort_formats(formats)
            info_dict['formats'] = formats
            return info_dict

        raise UnsupportedError(url)
