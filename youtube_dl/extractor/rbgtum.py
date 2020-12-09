from __future__ import unicode_literals

from .common import InfoExtractor


class RbgTumIE(InfoExtractor):
    _VALID_URL = r'https://live.rbg.tum.de/(?P<id>.*)'
    _TESTS = [{
        'url': 'https://live.rbg.tum.de/cgi-bin/streams/VOD/WiSe2021AutUFormSpr/2020_12_07_10_00/COMB',
        'md5': '12de44b7ad4ef491c1cc952fd4a0adc9',
        'info_dict': {
            'id': 'cgi-bin/streams/VOD/WiSe2021AutUFormSpr/2020_12_07_10_00/COMB',
            'ext': 'm3u8',
            'title': 'Aufzeichnung aus IRH102'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        hlsurl = self._html_search_regex('MMstartStream\\(.+, *\'(.+)\' *\\);', webpage, 'hlsurl')
        title = self._html_search_regex(r'<H2>(.+?)</H2>', webpage, 'title')

        return {
            'id': video_id,
            'title': title,
            'url': hlsurl,
        }
