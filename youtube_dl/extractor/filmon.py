# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import qualities
from ..compat import compat_urllib_request


_QUALITY = qualities(('low', 'high'))


class FilmOnIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?filmon\.com/(?:tv|channel)/(?P<id>[a-z0-9-]+)'
    _TESTS = [{
        'url': 'https://www.filmon.com/channel/filmon-sports',
        'only_matching': True,
    }, {
        'url': 'https://www.filmon.com/tv/2894',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        request = compat_urllib_request.Request('https://www.filmon.com/channel/%s' % (channel_id))
        request.add_header('X-Requested-With', 'XMLHttpRequest')
        channel_info = self._download_json(request, channel_id)
        now_playing = channel_info['now_playing']

        thumbnails = []
        for thumb in now_playing.get('images', ()):
            if thumb['type'] != '2':
                continue
            thumbnails.append({
                'url': thumb['url'],
                'width': int(thumb['width']),
                'height': int(thumb['height']),
            })

        formats = []

        for stream in channel_info['streams']:
            formats.append({
                'format_id': str(stream['id']),
                # this is an m3u8 stream, but we are deliberately not using _extract_m3u8_formats
                # because 0) it doesn't have bitrate variants anyway, and 1) the ids generated
                # by that method are highly unstable (because the bitrate is variable)
                'url': stream['url'],
                'resolution': stream['name'],
                'format_note': 'expires after %u seconds' % int(stream['watch-timeout']),
                'ext': 'mp4',
                'quality': _QUALITY(stream['quality']),
                'preference': int(stream['watch-timeout']),
            })
        self._sort_formats(formats)

        return {
            'id': str(channel_info['id']),
            'display_id': channel_info['alias'],
            'formats': formats,
            # XXX: use the channel description (channel_info['description'])?
            'uploader_id': channel_info['alias'],
            'uploader': channel_info['title'], # XXX: kinda stretching it...
            'title': now_playing.get('programme_name') or channel_info['title'],
            'description': now_playing.get('programme_description'),
            'thumbnails': thumbnails,
            'is_live': True,
        }


class FilmOnVODIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?filmon\.com/vod/view/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://www.filmon.com/vod/view/24869-0-plan-9-from-outer-space',
        'info_dict': {
            'id': '24869',
            'ext': 'mp4',
            'title': 'Plan 9 From Outer Space',
            'description': 'Dead human, zombies and vampires',
        },
    }, {
        'url': 'https://www.filmon.com/vod/view/2825-1-popeye-series-1',
        'info_dict': {
            'id': '2825',
            'title': 'Popeye Series 1',
        },
        'playlist_count': 8,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        result = self._download_json('https://www.filmon.com/api/vod/movie?id=%s' % (video_id), video_id)
        if result['code'] != 200:
            raise ExtractorError('FilmOn said: %s' % (result['reason']), expected=True)

        response = result['response']

        if response.get('episodes'):
            return {
                '_type': 'playlist',
                'id': video_id,
                'title': response['title'],
                'entries': [{
                    '_type': 'url',
                    'url': 'https://www.filmon.com/vod/view/%s' % (ep),
                } for ep in response['episodes']]
            }

        formats = []
        for (id, stream) in response['streams'].items():
            formats.append({
                'format_id': id,
                'url': stream['url'],
                'resolution': stream['name'],
                'format_note': 'expires after %u seconds' % int(stream['watch-timeout']),
                'ext': 'mp4',
                'quality': _QUALITY(stream['quality']),
                'preference': int(stream['watch-timeout']),
            })
        self._sort_formats(formats)

        poster = response['poster']
        thumbnails = [{
            'id': 'poster',
            'url': poster['url'],
            'width': poster['width'],
            'height': poster['height'],
        }]
        for (id, thumb) in poster['thumbs'].items():
            thumbnails.append({
                'id': id,
                'url': thumb['url'],
                'width': thumb['width'],
                'height': thumb['height'],
            })

        return {
            'id': video_id,
            'title': response['title'],
            'formats': formats,
            'description': response['description'],
            'thumbnails': thumbnails,
        }
