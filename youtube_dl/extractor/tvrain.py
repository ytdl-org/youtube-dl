# coding: utf-8
from __future__ import unicode_literals

import json

from .common import InfoExtractor
from ..utils import smuggle_url


class TVRainIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?tvrain\.ru.*/(?P<id>[a-z_]+-\d+)/?'
    _TESTS = [{
        'url': 'https://tvrain.ru/lite/teleshow/kak_vse_nachinalos/namin-418921/',
        'info_dict': {
            'id': '582306',
            'ext': 'mp4',
            'title': 'Стас Намин: «Мы нарушили девственность Кремля»',
            'duration': 3382,
        },
    }, {
        'url': 'https://tvrain.ru/teleshow/ted_dod/mozhete_li_vy_reshit_golovolomku_so_shkafchikami-432600/',
        'info_dict': {
            'id': '738482',
            'ext': 'mp4',
            'title': ' Можете ли вы решить головоломку со шкафчиками? ',
            'duration': 237,
        },
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        meta = self._search_regex(
            r'(?s)window\.TVRAIN\.app\s*=\s*({.+?})[\s\/\*\]>]+<\/script>',
            webpage, 'meta', default=None)

        if meta:
            article = json.loads(meta)['article']
            eagle_id = str(article['eagle_id'])
            return {
                '_type': 'url',
                'id': eagle_id,
                'ie_key': 'EaglePlatform',
                'url': smuggle_url(
                    'eagleplatform:tvrainru.media.eagleplatform.com:%s' % eagle_id,
                    {'referrer': url}),
            }

        return self.url_result(url, ie='Generic')
