# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none
)


class VGTRKIE(InfoExtractor):
    IE_DESC = 'ВГТРК'
    _VALID_URL = r'http://(?:.+?\.)?(?:vesti\.ru|russia2?\.tv|tvkultura\.ru|rutv\.ru)/(?P<id>.+)'

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
            'url': 'http://www.vesti.ru/doc.html?id=1349233',
            'info_dict': {
                'id': '773865',
                'ext': 'mp4',
                'title': 'Участники митинга штурмуют Донецкую областную администрацию',
                'description': 'md5:1a160e98b3195379b4c849f2f4958009',
                'duration': 210,
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
            'url': 'http://hitech.vesti.ru/news/view/id/4000',
            'info_dict': {
                'id': '766888',
                'ext': 'mp4',
                'title': 'Вести.net: интернет-гиганты начали перетягивание программных "одеял"',
                'description': 'md5:65ddd47f9830c4f42ed6475f8730c995',
                'duration': 279,
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
            'skip': 'Blocked outside Russia',
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
        },
        {
            'url': 'http://russia.tv/video/show/brand_id/5169/episode_id/970443/video_id/975648',
            'info_dict': {
                'id': '771852',
                'ext': 'mp4',
                'title': 'Прямой эфир. Жертвы загадочной болезни: смерть от старости в 17 лет',
                'description': 'md5:b81c8c55247a4bd996b43ce17395b2d8',
                'duration': 3096,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://russia.tv/brand/show/brand_id/57638',
            'info_dict': {
                'id': '774016',
                'ext': 'mp4',
                'title': 'Чужой в семье Сталина',
                'description': '',
                'duration': 2539,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://2.russia.tv/video/show/brand_id/48863/episode_id/972920/video_id/978667/viewtype/picture',
            'info_dict': {
                'id': '775081',
                'ext': 'mp4',
                'title': 'XXII зимние Олимпийские игры. Россияне заняли весь пьедестал в лыжных гонках',
                'description': 'md5:15d3741dd8d04b203fbc031c6a47fb0f',
                'duration': 101,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
            'skip': 'Blocked outside Russia',
        },
        {
            'url': 'http://tvkultura.ru/video/show/brand_id/31724/episode_id/972347/video_id/978186',
            'info_dict': {
                'id': '774471',
                'ext': 'mp4',
                'title': 'Монологи на все времена',
                'description': 'md5:18d8b5e6a41fb1faa53819471852d5d5',
                'duration': 2906,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
        {
            'url': 'http://rutv.ru/brand/show/id/6792/channel/75',
            'info_dict': {
                'id': '125521',
                'ext': 'mp4',
                'title': 'Грустная дама червей. Х/ф',
                'description': '',
                'duration': 4882,
            },
            'params': {
                # m3u8 download
                'skip_download': True,
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        mobj = re.search(
            r'<meta property="og:video" content="http://www\.vesti\.ru/i/flvplayer_videoHost\.swf\?vid=(?P<id>\d+)',
            page)
        if mobj:
            video_id = mobj.group('id')
            page = self._download_webpage('http://www.vesti.ru/only_video.html?vid=%s' % video_id, video_id,
                'Downloading video page')

        mobj = re.search(
            r'<meta property="og:video" content="http://player\.rutv\.ru/flash2v/container\.swf\?id=(?P<id>\d+)', page)
        if mobj:
            video_type = 'video'
            video_id = mobj.group('id')
        else:
            mobj = re.search(
                r'<iframe.+?src="http://player\.rutv\.ru/iframe/(?P<type>[^/]+)/id/(?P<id>\d+)[^"]*".*?></iframe>',
                page)

            if not mobj:
                raise ExtractorError('No media found', expected=True)

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
        width = int_or_none(media['width'])
        height = int_or_none(media['height'])
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