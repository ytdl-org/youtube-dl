# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class ChirbitIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?chirb\.it/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://chirb.it/PrIPv5',
        'md5': '9847b0dad6ac3e074568bf2cfb197de8',
        'info_dict': {
            'id': 'PrIPv5',
            'display_id': 'kukushtv_1423231243',
            'ext': 'mp3',
            'title': 'Фасадстрой',
            'url': 'http://audio.chirbit.com/kukushtv_1423231243.mp3'
        }
    }

    def _real_extract(self, url):
        audio_linkid = self._match_id(url)
        webpage = self._download_webpage(url, audio_linkid)

        audio_title = self._html_search_regex(r'<h2\s+itemprop="name">(.*?)</h2>', webpage, 'title')
        audio_id = self._html_search_regex(r'\("setFile",\s+"http://audio.chirbit.com/(.*?).mp3"\)', webpage, 'audio ID')
        audio_url = 'http://audio.chirbit.com/' + audio_id + '.mp3';

        return {
            'id': audio_linkid,
            'display_id': audio_id,
            'title': audio_title,
            'url': audio_url
        }
