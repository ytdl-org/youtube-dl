# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none
)


class VestiIE(InfoExtractor):
    IE_NAME = 'vesti'
    IE_DESC = 'Вести.Ru'
    _VALID_URL = r'http://(?:.+?\.)?vesti\.ru/(?P<id>.+)'

    _TESTS = [
        {
            'url': 'http://www.vesti.ru/videos?vid=575582&cid=1',
            'info_dict': {
                'id': '765035',
                'ext': 'mp4',
                'title': 'Вести.net: биткоины в России не являются законными',
                'description': 'md5:d4bb3859dc1177b28a94c5014c35a36b',
                'duration': 302,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.vesti.ru/only_video.html?vid=576180',
            'info_dict': {
                'id': '766048',
                'ext': 'mp4',
                'title': 'США заморозило, Британию затопило',
                'description': 'md5:f0ed0695ec05aed27c56a70a58dc4cc1',
                'duration': 87,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://sochi2014.vesti.ru/video/index/video_id/766403',
            'info_dict': {
                'id': '766403',
                'ext': 'mp4',
                'title': 'XXII зимние Олимпийские игры. Российские хоккеисты стартовали на Олимпиаде с победы',
                'description': 'md5:55805dfd35763a890ff50fa9e35e31b3',
                'duration': 271,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
            'skip': 'Blocked outside Russia'
        },
        {
            'url': 'http://sochi2014.vesti.ru/live/play/live_id/301',
            'info_dict': {
                'id': '51499',
                'ext': 'flv',
                'title': 'Сочи-2014. Биатлон. Индивидуальная гонка. Мужчины ',
                'description': 'md5:9e0ed5c9d2fa1efbfdfed90c9a6d179c',
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
            'skip': 'Translation has finished'
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        mobj = re.search(r'<meta property="og:video" content=".+?\.swf\?v?id=(?P<id>\d+).*?" />', page)
        if mobj:
            video_type = 'video'
            video_id = mobj.group('id')
        else:
            mobj = re.search(
                r'<iframe.+?src="http://player\.rutv\.ru/iframe/(?P<type>[^/]+)/id/(?P<id>\d+)[^"]*".*?></iframe>', page)

            if not mobj:
                raise ExtractorError('No media found')

            video_type = mobj.group('type')
            video_id = mobj.group('id')

        json_data = self._download_json(
            'http://player.rutv.ru/iframe/%splay/id/%s' % ('live-' if video_type == 'live' else '', video_id),
            video_id, 'Downloading JSON')

        if json_data['errors']:
            raise ExtractorError('vesti returned error: %s' % json_data['errors'], expected=True)

        playlist = json_data['data']['playlist']
        medialist = playlist['medialist']
        media = medialist[0]

        if media['errors']:
            raise ExtractorError('vesti returned error: %s' % media['errors'], expected=True)

        view_count = playlist.get('count_views')
        priority_transport = playlist['priority_transport']

        thumbnail = media['picture']
        width = media['width']
        height = media['height']
        description = media['anons']
        title = media['title']
        duration = int_or_none(media.get('duration'))

        formats = []

        for transport, links in media['sources'].items():
            for quality, url in links.items():
                if transport == 'rtmp':
                    mobj = re.search(r'^(?P<url>rtmp://[^/]+/(?P<app>.+))/(?P<playpath>.+)$', url)
                    if not mobj:
                        continue
                    fmt = {
                        'url': mobj.group('url'),
                        'play_path': mobj.group('playpath'),
                        'app': mobj.group('app'),
                        'page_url': 'http://player.rutv.ru',
                        'player_url': 'http://player.rutv.ru/flash2v/osmf.swf?i=22',
                        'rtmp_live': True,
                        'ext': 'flv',
                        'vbr': int(quality),
                    }
                elif transport == 'm3u8':
                    fmt = {
                        'url': url,
                        'ext': 'mp4',
                    }
                else:
                    fmt = {
                        'url': url
                    }
                fmt.update({
                    'width': width,
                    'height': height,
                    'format_id': '%s-%s' % (transport, quality),
                    'preference': -1 if priority_transport == transport else -2,
                })
                formats.append(fmt)

        if not formats:
            raise ExtractorError('No media links available for %s' % video_id)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'duration': duration,
            'formats': formats,
        }