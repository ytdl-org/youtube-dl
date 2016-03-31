# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    clean_html,
    xpath_text,
    int_or_none,
)


class NTVRuIE(InfoExtractor):
    IE_NAME = 'ntv.ru'
    _VALID_URL = r'https?://(?:www\.)?ntv\.ru/(?P<id>.+)'

    _TESTS = [
        {
            'url': 'http://www.ntv.ru/novosti/863142/',
            'md5': 'ba7ea172a91cb83eb734cad18c10e723',
            'info_dict': {
                'id': '746000',
                'ext': 'mp4',
                'title': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
                'description': 'Командующий Черноморским флотом провел переговоры в штабе ВМС Украины',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 136,
            },
        },
        {
            'url': 'http://www.ntv.ru/video/novosti/750370/',
            'md5': 'adecff79691b4d71e25220a191477124',
            'info_dict': {
                'id': '750370',
                'ext': 'mp4',
                'title': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
                'description': 'Родные пассажиров пропавшего Boeing не верят в трагический исход',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 172,
            },
        },
        {
            'url': 'http://www.ntv.ru/peredacha/segodnya/m23700/o232416',
            'md5': '82dbd49b38e3af1d00df16acbeab260c',
            'info_dict': {
                'id': '747480',
                'ext': 'mp4',
                'title': '«Сегодня». 21 марта 2014 года. 16:00',
                'description': '«Сегодня». 21 марта 2014 года. 16:00',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 1496,
            },
        },
        {
            'url': 'http://www.ntv.ru/kino/Koma_film',
            'md5': 'f825770930937aa7e5aca0dc0d29319a',
            'info_dict': {
                'id': '1007609',
                'ext': 'mp4',
                'title': 'Остросюжетный фильм «Кома»',
                'description': 'Остросюжетный фильм «Кома»',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 5592,
            },
        },
        {
            'url': 'http://www.ntv.ru/serial/Delo_vrachey/m31760/o233916/',
            'md5': '9320cd0e23f3ea59c330dc744e06ff3b',
            'info_dict': {
                'id': '751482',
                'ext': 'mp4',
                'title': '«Дело врачей»: «Деревце жизни»',
                'description': '«Дело врачей»: «Деревце жизни»',
                'thumbnail': 're:^http://.*\.jpg',
                'duration': 2590,
            },
        },
    ]

    _VIDEO_ID_REGEXES = [
        r'<meta property="og:url" content="http://www\.ntv\.ru/video/(\d+)',
        r'<video embed=[^>]+><id>(\d+)</id>',
        r'<video restriction[^>]+><key>(\d+)</key>',
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        video_id = self._html_search_regex(self._VIDEO_ID_REGEXES, webpage, 'video id')

        player = self._download_xml(
            'http://www.ntv.ru/vi%s/' % video_id,
            video_id, 'Downloading video XML')
        title = clean_html(xpath_text(player, './data/title', 'title', fatal=True))
        description = clean_html(xpath_text(player, './data/description', 'description'))

        video = player.find('./data/video')
        video_id = xpath_text(video, './id', 'video id')
        thumbnail = xpath_text(video, './splash', 'thumbnail')
        duration = int_or_none(xpath_text(video, './totaltime', 'duration'))
        view_count = int_or_none(xpath_text(video, './views', 'view count'))

        token = self._download_webpage(
            'http://stat.ntv.ru/services/access/token',
            video_id, 'Downloading access token')

        formats = []
        for format_id in ['', 'hi', 'webm']:
            file_ = video.find('./%sfile' % format_id)
            if file_ is None:
                continue
            size = video.find('./%ssize' % format_id)
            formats.append({
                'url': 'http://media2.ntv.ru/vod/%s&tok=%s' % (file_.text, token),
                'filesize': int_or_none(size.text if size is not None else None),
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
