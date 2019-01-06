# coding: utf-8
from __future__ import unicode_literals

import hashlib
from .common import InfoExtractor
from ..utils import parse_duration


class MallTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mall\.tv/(?:.+/)?(?P<id>.+)'
    _TESTS = [
        {
            'url': 'https://www.mall.tv/18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice',
            'md5': '9ced0de056534410837077e23bfba796',
            'info_dict': {
                'id': 'af7649e93dc6a2a04198e6c8143605a4',
                'ext': 'mp4',
                'title': '18 miliard pro neziskovky. Opravdu jsou sportovci nebo Člověk v tísni pijavice?',
                'description': ('Pokud někdo hospodaří s penězmi daňových '
                                'poplatníků, pak logicky chceme vědět, jak s '
                                'nimi nakládá. Objem dotací pro neziskovky '
                                'roste, ale opravdu jsou tyto organizace '
                                '„pijavice", jak o nich hovoří And')
                }
        },
        {
            'url': 'https://www.mall.tv/kdo-to-plati/18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice',
            'md5': '9ced0de056534410837077e23bfba796',
            'info_dict': {
                'id': 'af7649e93dc6a2a04198e6c8143605a4',
                'ext': 'mp4',
                'title': '18 miliard pro neziskovky. Opravdu jsou sportovci nebo Člověk v tísni pijavice?',
                'description': ('Pokud někdo hospodaří s penězmi daňových '
                                'poplatníků, pak logicky chceme vědět, jak s '
                                'nimi nakládá. Objem dotací pro neziskovky '
                                'roste, ale opravdu jsou tyto organizace '
                                '„pijavice", jak o nich hovoří And')
                }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        info = self._search_json_ld(webpage, video_id, default={})

        format_url = self._html_search_regex(
            r'<source src=([\"\'])?(?P<src>.+?index)\1?[^>]*?>',
            webpage, 'm3u8 URL', group='src')
        formats = self._extract_m3u8_formats(format_url+'.m3u8',
                                             video_id, 'mp4')
        self._sort_formats(formats)
        thumbnail = info.get('thumbnailUrl', self._og_search_thumbnail(webpage))
        duration = parse_duration(info.get('duration'))
        result = {
            'id': hashlib.md5(video_id).hexdigest().decode('utf8'),
            'title': info.get('name', self._og_search_title(webpage)),
            'description': self._og_search_description(webpage),
            'formats': formats
        }
        if thumbnail:
            result.update({'thumbnail': thumbnail})
        if duration:
            result.update({'duration': duration})

        return result
