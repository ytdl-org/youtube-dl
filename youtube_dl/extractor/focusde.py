# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor

from ..utils import (
    int_or_none
)


class FocusDeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?focus\.de\/(?:[\w-]+\/)*[\w-]+_id_(?P<id>\d+)\.html'

    _TESTS = [
        {
            'url': 'https://www.focus.de/finanzen/nicht-vorspuelen-warum-sie-verschmutztes-geschirr-nie-abwaschen-sollten-bevor-sie-es-in-die-spuelmaschine-stellen_id_8673152.html',
            'md5': 'c081f2bcbb1868241148ec5634101f85',
            'info_dict': {
                'id': '8673152',
                'ext': 'mp4',
                'title': 'Warum man Geschirr nicht abwaschen sollte, bevor man es in Sp\xfclmaschine stellt',
                'upload_date': '20190219',
                'timestamp': 1550577960,
                'duration': 68
            }
        },
        {
            'url': 'https://www.focus.de/kultur/kino_tv/gntm-2019-das-ziehe-ich-nicht-an-topmodel-kandidatinnen-verzweifeln-an-dessous-shooting_id_10359434.html',
            'md5': 'f5531050aeb43333220ce0e0b26ad109',
            'info_dict': {
                'id': '10359434',
                'ext': 'mp4',
                'title': 'GNTM 2019: Topmodel-Kandidatinnen verzweifeln an sexy Dessous-Shooting',
                'upload_date': '20190222',
                'timestamp': 1550825580,
                'duration': 606
            }
        },
        {
            'url': 'https://www.focus.de/sport/fussball/bundesliga1/wertvoll-unter-vorbehalt-fc-bayern-fuer-hummels-ist-bei-bayern-nur-unter-einer-bedingung-platz_id_10360615.html',
            'md5': '77277c64c087a70993ae15457f8f3a8f',
            'info_dict': {
                'id': '10360615',
                'ext': 'mp4',
                'title': 'FC Bayern: F\xfcr Hummels ist nur unter einer Bedingung Platz',
                'upload_date': '20190222',
                'timestamp': 1550844240,
                'duration': 59
            }
        }
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        info = self._search_json_ld(webpage, video_id)
        self.report_extraction(video_id)

        video_url = self._html_search_meta('fol:video-url', webpage, 'url', default=None)
        duration = int_or_none(self._html_search_meta('fol:video-duration', webpage, 'duration', default=None))

        info.update({
            'id': video_id,
            'url': video_url,
            'duration': duration
        })

        if video_url:
            return info
