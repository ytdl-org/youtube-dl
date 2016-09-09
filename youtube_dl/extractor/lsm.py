# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class LSMIE(InfoExtractor):
    _VALID_URL = r'http://(?:www\.)?ltv\.lsm\.lv/lv/raksts/.+id(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://ltv.lsm.lv/lv/raksts/08.09.2016-adreses.-latvijas-nacionala-biblioteka-un-vasarnica-pabazos.id79498/',
        'info_dict': {
            'id': '79498',
            'title': 'Adreses. Latvijas Nacionālā bibliotēka un vasarnīca Pabažos',
            'thumbnail': 're:^https?://.*\.jpg$',
            'description': 'Pirmajā sērijā kopā ar ceļabiedru Daini Īvānu Mārtiņš Ķibilds ļaus salīdzināt divas šķietami nesalīdzināmas adreses – Gunāra Birkerta Latvijas Nacionālo bibliotēku un daudz mazāk zināmo (un arī izmēros daudz mazāko) Modra Ģelža vasarnīcu Pabažos. Divi leģendāri arhitekti, divas simboliskas celtnes, un unikāla iespēja tās ieraudzīt cita simbola – Atmodas simbola Daiņa Īvāna – acīm.',
            'ext': 'mp4',
        },
        'params': {
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage).strip()
        thumbnail = self._og_search_thumbnail(webpage)
        description = self._og_search_description(webpage).strip()

        video_url = self._search_regex(
            r"\"(http://s\.ltv\.lv:1935/vod/[^\"]+)\"",
            webpage, 'video URL')

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': description,
            'ext': 'mp4',
            'url': video_url,
        }
