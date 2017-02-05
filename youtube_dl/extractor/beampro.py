# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    compat_str,
    int_or_none,
    parse_iso8601,
    try_get,
)


class BeamProLiveIE(InfoExtractor):
    IE_NAME = 'Beam:live'
    _VALID_URL = r'https?://(?:\w+\.)?beam\.pro/(?P<id>[^/?#&]+)'
    _RATINGS = {'family': 0, 'teen': 13, '18+': 18}
    _TEST = {
        'url': 'http://www.beam.pro/niterhayven',
        'info_dict': {
            'id': '261562',
            'ext': 'mp4',
            'title': 'Introducing The Witcher 3 //  The Grind Starts Now!',
            'description': 'md5:0b161ac080f15fe05d18a07adb44a74d',
            'thumbnail': r're:https://.*\.jpg$',
            'timestamp': 1483477281,
            'upload_date': '20170103',
            'uploader': 'niterhayven',
            'uploader_id': '373396',
            'age_limit': 18,
            'is_live': True,
            'view_count': int,
        },
        'skip': 'niterhayven is offline',
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        channel_name = self._match_id(url)

        chan = self._download_json(
            'https://beam.pro/api/v1/channels/%s' % channel_name, channel_name)

        if chan.get('online') is False:
            raise ExtractorError(
                '{0} is offline'.format(channel_name), expected=True)

        channel_id = chan['id']

        formats = self._extract_m3u8_formats(
            'https://beam.pro/api/v1/channels/%s/manifest.m3u8' % channel_id,
            channel_name, ext='mp4', m3u8_id='hls', fatal=False)
        self._sort_formats(formats)

        user_id = chan.get('userId') or try_get(chan, lambda x: x['user']['id'])

        return {
            'id': compat_str(chan.get('id') or channel_name),
            'title': self._live_title(chan.get('name') or channel_name),
            'description': clean_html(chan.get('description')),
            'thumbnail': try_get(chan, lambda x: x['thumbnail']['url'], compat_str),
            'timestamp': parse_iso8601(chan.get('updatedAt')),
            'uploader': chan.get('token') or try_get(
                chan, lambda x: x['user']['username'], compat_str),
            'uploader_id': compat_str(user_id) if user_id else None,
            'age_limit': self._RATINGS.get(chan.get('audience')),
            'is_live': True,
            'view_count': int_or_none(chan.get('viewersTotal')),
            'formats': formats,
        }
