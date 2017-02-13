# coding: utf-8
from __future__ import unicode_literals

from .onet import OnetBaseIE
from ..utils import clean_html


class VODPlIE(OnetBaseIE):
    _VALID_URL = r'https?://vod\.pl/(?:.*/)?(?P<id>[0-9a-zA-Z]+)'

    _TEST = {
        'url': 'https://vod.pl/filmy/chlopaki-nie-placza/3ep3jns',
        'md5': 'a7dc3b2f7faa2421aefb0ecaabf7ec74',
        'info_dict': {
            'id': '3ep3jns',
            'ext': 'mp4',
            'title': 'Chłopaki nie płaczą',
            'description': 'Kuba Brenner aby pomóc swojemu nieśmiałemu przyjacielowi Oskarowi wynajmuje w agencji towarzyskiej dwie panie. Po upojnej nocy okazuje się, że chłopcy nie byli przygotowani finansowo. "Opiekun artystyczny" dziewczyn zabiera w ramach rekompensaty drogocenną rzeźbę należącą do wujka Oskara. Kłopoty chłopców zaczynają się, gdy Kuba udaje się do agencji aby wykupić figurkę i trafia w sam środek mafijnej transakcji... Idiotyczny przypadek sprawia, że w klubie dochodzi do strzelaniny podczas której Grucha i Bolec zostają ranni, ginie również walizka z pieniędzmi... Podejrzenie pada na Kubę.',
            'timestamp': 1463415154,
            'duration': 5765,
            'upload_date': '20160516',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        mvp_id = self._search_mvp_id(webpage)

        info_dict = self._extract_from_id(mvp_id, webpage)
        info_dict.update({
            'id': video_id,
            'description': clean_html(info_dict['description']).strip().replace('\r', '\n')
        })

        return info_dict
