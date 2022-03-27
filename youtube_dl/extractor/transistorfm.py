# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import unescapeHTML


class TransistorFMIE(InfoExtractor):
    _VALID_URL = r'https://share.transistor.fm/s/(?P<id>[0-9a-f]{8})'
    _TEST = {
        'url': 'https://share.transistor.fm/s/e9d040c0',
        'md5': '78ff1cdee96b923b6eee0f43a231352b',
        'info_dict': {
            'id': 'e9d040c0',
            'ext': 'mp3',
            'duration': 1132,
            'artist': 'Батенька, да вы трансформер',
            'title': 'Эпизод 19. Люди и фанатики',
            'description': ('Мы продолжаем спорить о роли религии в нашей '
                            'жизни, и сегодняшние наши герои  —  люди, '
                            'попавшие в плен. Кто-то застрял в серьёзной секте'
                            ', а кто-то просто любит ритуалы больше, чем людей'
                            '. Но всем приходится от этого несладко.\r\n'
                            '\r\n'
                            '01:21 — Марина. Выросла среди людей, которые '
                            'жгут книги про Гарри Поттера\r\n'
                            '05:09 — Афина. Дочка мамы-фанатички\r\n'
                            '10:05 — … и к тридцати годам они полностью '
                            'перестали друг друга понимать\r\n'
                            '12:02 — Наталья.  Вот у неё поначалу всё было '
                            'хорошо…\r\n'
                            '13:40 — ...но потом мужа затянуло в секту'),
            'thumbnail': 'https://images.transistor.fm/file/transistor/images/episode/373966/medium_1602593993-artwork.jpg',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        data = self._parse_json(unescapeHTML(self._search_regex(
            r'\s*<div id="embed-app" data-episodes="(.+?)" data-show="',
            webpage, 'JSON data block')), video_id)[0]

        return {
            'id': video_id,
            'title': data.get('title'),
            'description': data.get('formatted_summary'),
            'thumbnail': data.get('artwork'),
            'duration': data.get('duration'),
            'artist': data.get('author'),
            'url': data.get('trackable_media_url'),
        }
