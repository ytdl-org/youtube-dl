# encoding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class FazIE(InfoExtractor):
    IE_NAME = 'faz.net'
    _VALID_URL = r'https?://www\.faz\.net/multimedia/videos/.*?-(?P<id>\d+)\.html'

    _TEST = {
        'url': 'http://www.faz.net/multimedia/videos/stockholm-chemie-nobelpreis-fuer-drei-amerikanische-forscher-12610585.html',
        'info_dict': {
            'id': '12610585',
            'ext': 'mp4',
            'title': 'Stockholm: Chemie-Nobelpreis für drei amerikanische Forscher',
            'description': 'md5:1453fbf9a0d041d985a47306192ea253',
        },
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        config_xml_url = self._search_regex(
            r'writeFLV\(\'(.+?)\',', webpage, 'config xml url')
        config = self._download_xml(
            config_xml_url, video_id, 'Downloading config xml')

        encodings = config.find('ENCODINGS')
        formats = []
        for pref, code in enumerate(['LOW', 'HIGH', 'HQ']):
            encoding = encodings.find(code)
            if encoding is None:
                continue
            encoding_url = encoding.find('FILENAME').text
            formats.append({
                'url': encoding_url,
                'format_id': code.lower(),
                'quality': pref,
            })
        self._sort_formats(formats)

        descr = self._html_search_regex(
            r'<p class="Content Copy">(.*?)</p>', webpage, 'description', fatal=False)
        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': descr,
            'thumbnail': config.find('STILL/STILL_BIG').text,
        }
