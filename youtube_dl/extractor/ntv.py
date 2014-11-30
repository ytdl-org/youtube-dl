# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    unescapeHTML
)


class NTVIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ntv\.ru/(?P<id>.+)'

    _TESTS = [
        {
            'url': 'http://www.ntv.ru/novosti/863142/',
            'info_dict': {
                'id': '746000',
                'ext': 'flv',
                'title': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
                'description': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
                'duration': 136,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ntv.ru/video/novosti/750370/',
            'info_dict': {
                'id': '750370',
                'ext': 'flv',
                'title': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
                'description': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
                'duration': 172,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ntv.ru/peredacha/segodnya/m23700/o232416',
            'info_dict': {
                'id': '747480',
                'ext': 'flv',
                'title': '«Сегодня». 21 марта 2014 года. 16:00 ',
                'description': '«Сегодня». 21 марта 2014 года. 16:00 ',
                'duration': 1496,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ntv.ru/kino/Koma_film',
            'info_dict': {
                'id': '758100',
                'ext': 'flv',
                'title': 'Остросюжетный фильм «Кома»',
                'description': 'Остросюжетный фильм «Кома»',
                'duration': 5592,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
        {
            'url': 'http://www.ntv.ru/serial/Delo_vrachey/m31760/o233916/',
            'info_dict': {
                'id': '751482',
                'ext': 'flv',
                'title': '«Дело врачей»: «Деревце жизни»',
                'description': '«Дело врачей»: «Деревце жизни»',
                'duration': 2590,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            },
        },
    ]

    _VIDEO_ID_REGEXES = [
        r'<meta property="og:url" content="http://www\.ntv\.ru/video/(\d+)',
        r'<video embed=[^>]+><id>(\d+)</id>',
        r'<video restriction[^>]+><key>(\d+)</key>',
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id)

        video_id = self._html_search_regex(self._VIDEO_ID_REGEXES, page, 'video id')

        player = self._download_xml('http://www.ntv.ru/vi%s/' % video_id, video_id, 'Downloading video XML')
        title = unescapeHTML(player.find('./data/title').text)
        description = unescapeHTML(player.find('./data/description').text)

        video = player.find('./data/video')
        video_id = video.find('./id').text
        thumbnail = video.find('./splash').text
        duration = int(video.find('./totaltime').text)
        view_count = int(video.find('./views').text)
        puid22 = video.find('./puid22').text

        apps = {
            '4': 'video1',
            '7': 'video2',
        }

        app = apps.get(puid22, apps['4'])

        formats = []
        for format_id in ['', 'hi', 'webm']:
            file = video.find('./%sfile' % format_id)
            if file is None:
                continue
            size = video.find('./%ssize' % format_id)
            formats.append({
                'url': 'rtmp://media.ntv.ru/%s' % app,
                'app': app,
                'play_path': file.text,
                'rtmp_conn': 'B:1',
                'player_url': 'http://www.ntv.ru/swf/vps1.swf?update=20131128',
                'page_url': 'http://www.ntv.ru',
                'flash_ver': 'LNX 11,2,202,341',
                'rtmp_live': True,
                'ext': 'flv',
                'filesize': int(size.text),
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }
