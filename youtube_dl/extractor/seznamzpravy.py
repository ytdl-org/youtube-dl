# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    urljoin,
    int_or_none,
)


class SeznamZpravyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?seznam\.cz/zpravy/clanek/(?:[-a-z0-9]+)-(?P<id>[0-9]+)'
    _API_URL = 'https://apiclanky.seznam.cz/'
    _MAGIC_SUFFIX = 'spl2,2,VOD'

    _TESTS = [{
        # video with SDN URL
        'url': 'https://www.seznam.cz/zpravy/clanek/jejich-svet-na-nas-utoci-je-lepsi-branit-se-na-jejich-pisecku-rika-reziser-a-major-v-zaloze-marhoul-35990',
        'md5': '855f9fed87bd93e48775d59671a3a3e3',
        'info_dict': {
            'id': '35990',
            'ext': 'mp4',
            'title': 'Svět bez obalu: Rozhovor s Václavem Marhoulem o zahraničních vojenských misích a aktivních zálohách.',
            'description': 'O nasazení českých vojáků v zahraničí. Marhoul by na mise posílal i zálohy. „Nejdříve se ale musí vycvičit,“ říká.',
        }
    }, {
        # video with live stream URL
        'url': 'https://www.seznam.cz/zpravy/clanek/znovu-do-vlady-s-ano-pavel-belobradek-ve-volebnim-specialu-seznamu-38489',
        'md5': '3da261b41d776b2c860c191f47517057',
        'info_dict': {
            'id': '38489',
            'ext': 'mp4',
            'title': 'Předseda KDU-ČSL Pavel Bělobrádek ve volební Výzvě Seznamu.',
            'description': 'Předvolební rozhovory s lídry deseti hlavních stran pokračují. Ve Výzvě Jindřicha Šídla odpovídal předseda lidovců Pavel Bělobrádek.',
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        data = self._download_json(self._API_URL + 'v1/documents/' + video_id, video_id)

        if 'video' in data['caption']:
            sdn_url = data['caption']['video']['sdn'] + self._MAGIC_SUFFIX
        else:
            sdn_url = self._download_json(data['caption']['liveStreamUrl'] + self._MAGIC_SUFFIX, video_id)['Location']

        formats = []
        for fmt, fmtdata in self._download_json(sdn_url, video_id)['data']['mp4'].items():
            relative_url = fmtdata.get('url')
            if not relative_url:
                continue

            try:
                width, height = fmtdata.get('resolution')
            except TypeError:
                width, height = None, None

            formats.append({
                'format_id': fmt,
                'width': int_or_none(width),
                'height': int_or_none(height),
                'url': urljoin(sdn_url, relative_url),
            })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': data['captionTitle'],
            'description': data.get('perex'),
            'formats': formats,
        }
