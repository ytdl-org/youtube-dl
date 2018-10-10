# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import parse_duration


class MallTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mall\.tv/(?:.+/)?(?P<id>.+)'
    _TESTS = [
        {
            'url': ('https://www.mall.tv/18-miliard-pro-neziskovky'
                    '-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice'),
            'info_dict': {
                'id': ('18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-'
                       'clovek-v-tisni-pijavice'),
                'ext': 'mp4',
                'title': ('18 miliard pro neziskovky. Opravdu jsou sportovci '
                          'nebo Člověk v tísni pijavice?'),
                'description': ('Pokud někdo hospodaří s penězmi daňových '
                                'poplatníků, pak logicky chceme vědět, jak s '
                                'nimi nakládá. Objem dotací pro neziskovky '
                                'roste, ale opravdu jsou tyto organizace '
                                '„pijavice", jak o nich hovoří And')
                },
            'params': {
                'skip_download': True
            }
        },
        {
            'url': ('https://www.mall.tv/kdo-to-plati/18-miliard-pro-neziskovky'
                    '-opravdu-jsou-sportovci-nebo-clovek-v-tisni-pijavice'),
            'info_dict': {
                'id': ('18-miliard-pro-neziskovky-opravdu-jsou-sportovci-nebo-'
                       'clovek-v-tisni-pijavice'),
                'ext': 'mp4',
                'title': ('18 miliard pro neziskovky. Opravdu jsou sportovci '
                          'nebo Člověk v tísni pijavice?'),
                'description': ('Pokud někdo hospodaří s penězmi daňových '
                                'poplatníků, pak logicky chceme vědět, jak s '
                                'nimi nakládá. Objem dotací pro neziskovky '
                                'roste, ale opravdu jsou tyto organizace '
                                '„pijavice", jak o nich hovoří And')
                },
            'params': {
                'skip_download': True
            }
        },
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
        title = info.get('title', self._og_search_title(webpage, fatal=False))
        thumbnail = info.get('thumbnailUrl', self._og_search_thumbnail(webpage))
        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'description': self._og_search_description(webpage),
            'duration': parse_duration(info.get('duration')),
            'formats': formats
        }
