# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    clean_html,
    compat_str,
    float_or_none,
    int_or_none,
    parse_iso8601,
    try_get,
    urljoin,
)


class BeamProBaseIE(InfoExtractor):
    _API_BASE = 'https://mixer.com/api/v1'
    _RATINGS = {'family': 0, 'teen': 13, '18+': 18}

    def _extract_channel_info(self, chan):
        user_id = chan.get('userId') or try_get(chan, lambda x: x['user']['id'])
        return {
            'uploader': chan.get('token') or try_get(
                chan, lambda x: x['user']['username'], compat_str),
            'uploader_id': compat_str(user_id) if user_id else None,
            'age_limit': self._RATINGS.get(chan.get('audience')),
        }


class BeamProLiveIE(BeamProBaseIE):
    IE_NAME = 'Mixer:live'
    _VALID_URL = r'https?://(?:\w+\.)?(?:beam\.pro|mixer\.com)/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://mixer.com/niterhayven',
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

    _MANIFEST_URL_TEMPLATE = '%s/channels/%%s/manifest.%%s' % BeamProBaseIE._API_BASE

    @classmethod
    def suitable(cls, url):
        return False if BeamProVodIE.suitable(url) else super(BeamProLiveIE, cls).suitable(url)

    def _real_extract(self, url):
        channel_name = self._match_id(url)

        chan = self._download_json(
            '%s/channels/%s' % (self._API_BASE, channel_name), channel_name)

        if chan.get('online') is False:
            raise ExtractorError(
                '{0} is offline'.format(channel_name), expected=True)

        channel_id = chan['id']

        def manifest_url(kind):
            return self._MANIFEST_URL_TEMPLATE % (channel_id, kind)

        formats = self._extract_m3u8_formats(
            manifest_url('m3u8'), channel_name, ext='mp4', m3u8_id='hls',
            fatal=False)
        formats.extend(self._extract_smil_formats(
            manifest_url('smil'), channel_name, fatal=False))
        self._sort_formats(formats)

        info = {
            'id': compat_str(chan.get('id') or channel_name),
            'title': self._live_title(chan.get('name') or channel_name),
            'description': clean_html(chan.get('description')),
            'thumbnail': try_get(
                chan, lambda x: x['thumbnail']['url'], compat_str),
            'timestamp': parse_iso8601(chan.get('updatedAt')),
            'is_live': True,
            'view_count': int_or_none(chan.get('viewersTotal')),
            'formats': formats,
        }
        info.update(self._extract_channel_info(chan))

        return info


class BeamProVodIE(BeamProBaseIE):
    IE_NAME = 'Mixer:vod'
    _VALID_URL = r'https?://(?:\w+\.)?(?:beam\.pro|mixer\.com)/[^/?#&]+\?.*?\bvod=(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://mixer.com/willow8714?vod=2259830',
        'md5': 'b2431e6e8347dc92ebafb565d368b76b',
        'info_dict': {
            'id': '2259830',
            'ext': 'mp4',
            'title': 'willow8714\'s Channel',
            'duration': 6828.15,
            'thumbnail': r're:https://.*source\.png$',
            'timestamp': 1494046474,
            'upload_date': '20170506',
            'uploader': 'willow8714',
            'uploader_id': '6085379',
            'age_limit': 13,
            'view_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://mixer.com/streamer?vod=IxFno1rqC0S_XJ1a2yGgNw',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_format(vod, vod_type):
        if not vod.get('baseUrl'):
            return []

        if vod_type == 'hls':
            filename, protocol = 'manifest.m3u8', 'm3u8_native'
        elif vod_type == 'raw':
            filename, protocol = 'source.mp4', 'https'
        else:
            assert False

        data = vod.get('data') if isinstance(vod.get('data'), dict) else {}

        format_id = [vod_type]
        if isinstance(data.get('Height'), compat_str):
            format_id.append('%sp' % data['Height'])

        return [{
            'url': urljoin(vod['baseUrl'], filename),
            'format_id': '-'.join(format_id),
            'ext': 'mp4',
            'protocol': protocol,
            'width': int_or_none(data.get('Width')),
            'height': int_or_none(data.get('Height')),
            'fps': int_or_none(data.get('Fps')),
            'tbr': int_or_none(data.get('Bitrate'), 1000),
        }]

    def _real_extract(self, url):
        vod_id = self._match_id(url)

        vod_info = self._download_json(
            '%s/recordings/%s' % (self._API_BASE, vod_id), vod_id)

        state = vod_info.get('state')
        if state != 'AVAILABLE':
            raise ExtractorError(
                'VOD %s is not available (state: %s)' % (vod_id, state),
                expected=True)

        formats = []
        thumbnail_url = None

        for vod in vod_info['vods']:
            vod_type = vod.get('format')
            if vod_type in ('hls', 'raw'):
                formats.extend(self._extract_format(vod, vod_type))
            elif vod_type == 'thumbnail':
                thumbnail_url = urljoin(vod.get('baseUrl'), 'source.png')

        self._sort_formats(formats)

        info = {
            'id': vod_id,
            'title': vod_info.get('name') or vod_id,
            'duration': float_or_none(vod_info.get('duration')),
            'thumbnail': thumbnail_url,
            'timestamp': parse_iso8601(vod_info.get('createdAt')),
            'view_count': int_or_none(vod_info.get('viewsTotal')),
            'formats': formats,
        }
        info.update(self._extract_channel_info(vod_info.get('channel') or {}))

        return info
