# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    extract_attributes,
    urlencode_postdata,
    ExtractorError,
)


class TVPlayerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tvplayer\.com/watch/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://tvplayer.com/watch/bbcone',
        'info_dict': {
            'id': '89',
            'ext': 'mp4',
            'title': r're:^BBC One [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        }
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        current_channel = extract_attributes(self._search_regex(
            r'(<div[^>]+class="[^"]*current-channel[^"]*"[^>]*>)',
            webpage, 'channel element'))
        title = current_channel['data-name']

        resource_id = self._search_regex(
            r'resourceId\s*=\s*"(\d+)"', webpage, 'resource id')
        platform = self._search_regex(
            r'platform\s*=\s*"([^"]+)"', webpage, 'platform')
        token = self._search_regex(
            r'token\s*=\s*"([^"]+)"', webpage, 'token', default='null')
        validate = self._search_regex(
            r'validate\s*=\s*"([^"]+)"', webpage, 'validate', default='null')

        try:
            response = self._download_json(
                'http://api.tvplayer.com/api/v2/stream/live',
                resource_id, headers={
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                }, data=urlencode_postdata({
                    'service': 1,
                    'platform': platform,
                    'id': resource_id,
                    'token': token,
                    'validate': validate,
                }))['tvplayer']['response']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError):
                response = self._parse_json(
                    e.cause.read().decode(), resource_id)['tvplayer']['response']
                raise ExtractorError(
                    '%s said: %s' % (self.IE_NAME, response['error']), expected=True)
            raise

        formats = self._extract_m3u8_formats(response['stream'], resource_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': resource_id,
            'display_id': display_id,
            'title': self._live_title(title),
            'formats': formats,
            'is_live': True,
        }
