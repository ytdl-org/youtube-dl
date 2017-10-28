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
        'url': 'https://www.seznam.cz/zpravy/clanek/jejich-svet-na-nas-utoci-je-lepsi-branit-se-na-jejich-pisecku-rika-reziser-a-major-v-zaloze-marhoul-35990',
        'md5': '855f9fed87bd93e48775d59671a3a3e3',
        'info_dict': {
            'id': '35990',
            'ext': 'mp4',
            'title': 'Svět bez obalu: Rozhovor s Václavem Marhoulem o zahraničních vojenských misích a aktivních zálohách.',
            'description': 'O nasazení českých vojáků v zahraničí. Marhoul by na mise posílal i zálohy. „Nejdříve se ale musí vycvičit,“ říká.',
        }
    }, {
        'url': 'https://www.seznam.cz/zpravy/clanek/vyzva-volicum-letos-se-na-to-klidne-vykaslete-kdyby-mohly-volby-neco-zmenit-davno-by-je-prece-zakazali-38474',
        'md5': '542ebc27baa3b2dd99d1671c12f5b28c',
        'info_dict': {
            'id': '38474',
            'ext': 'mp4',
            'title': 'Šťastné pondělí Jindřicha Šídla.',
            'description': 'Do voleb zbývají čtyři dny. Jindřich Šídlo proto přichází se zásadním doporučením voličům, jak se letos zachovat. Další díl satirického pořadu.',
        }
    }, {
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
        api_url = self._API_URL + 'v1/documents/{}'.format(video_id)
        data = self._download_json(api_url, video_id)

        if 'video' in data['caption']:
            sdn_url = data['caption']['video']['sdn'] + self._MAGIC_SUFFIX
        else:
            location_url = data['caption']['liveStreamUrl'] + self._MAGIC_SUFFIX
            sdn_url = self._download_json(location_url, video_id)['Location']

        sdn_data = self._download_json(sdn_url, video_id)

        formats = []
        for fmt, fmtdata in sdn_data['data']['mp4'].items():
            resolution = fmtdata.get('resolution')
            formats.append({
                'format_id': fmt,
                'width': int_or_none(resolution[0]) if resolution is not None else None,
                'height': int_or_none(resolution[1]) if resolution is not None else None,
                'url': urljoin(sdn_url, fmtdata['url']),
            })

        formats.sort(key=lambda x: x['height'])

        return {
            'id': video_id,
            'title': data['captionTitle'],
            'description': data.get('perex'),
            'formats': formats,
        }
