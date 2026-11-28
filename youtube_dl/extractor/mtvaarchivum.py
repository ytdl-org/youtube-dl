# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class MtvaArchivumIE(InfoExtractor):
    _VALID_URL = r'https://archivum\.mtva\.hu\/m3/(?P<id>M3-[a-zA-Z0-9]*)'
    _TESTS = [{
        'url': 'https://archivum.mtva.hu/m3/M3-87720998249999359',
        'info_dict': {
            'id': 'M3-87720998249999359',
            'ext': 'mp4',
            'title': 'Kék egér',
            'description': 'Kék egér nem sokáig örülhet a napsütésnek, mert egy kölyökkutya azt hiszi, kutyáknak való játék ez a kék valami. A Kék egér tiltakozása ellenére csak akkor engedi el az egeret, amikor az elásott csontja helyét megtalálja a kutya. A menekülő egérke elbotlik egy fél perecben aminek nagyon megörül, de egy erőszakos galamb meghívatja magát a perecre. Némi ellenszolgáltatás, és egy jó tanács fejében az egészet felfalja.',
        },
    }, {
        'url': 'https://archivum.mtva.hu/m3/M3-59898941410999595',
        'info_dict': {
            'id': 'M3-59898941410999595',
            'ext': 'mp4',
            'title': 'Magyar retro',
            'description': 'MTVA Archívum',
        }
    }, {
        'url': 'https://archivum.mtva.hu/m3/M3-59968988460999294',
        'info_dict': {
            'id': 'M3-59968988460999294',
            'ext': 'mp4',
            'title': 'FŐTÉR',
            'description': 'MTVA Archívum',
        }
    }, {
        'url': 'https://archivum.mtva.hu/m3/M3-599A8939770999694',
        'info_dict': {
            'id': 'M3-599A8939770999694',
            'ext': 'mp4',
            'title': 'Csináljuk a fesztivált!',
            'description': 'MTVA Archívum',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        json = self._download_json('https://archivum.mtva.hu/m3/stream?no_lb=1&target=' + video_id, video_id)
        video_url = json['url']
        title = self._og_search_title(webpage) or self._html_search_regex(
            '<h1 class=\"active-title\">.+</h1>', webpage, 'title')
        description = self._og_search_description(webpage) or self._html_search_regex(
            '<p class=\"active-full-description\">\n.+</p>', webpage, 'description')
        thumbnail = self._og_search_thumbnail(webpage)

        formats = self._extract_m3u8_formats(
            video_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'formats': formats,
        }
