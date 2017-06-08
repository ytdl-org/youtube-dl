# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    decode_packed_codes,
    PACKED_CODES_RE, encode_base_n, ExtractorError)


class AsBookIE(InfoExtractor):
    _VIDEO_RE = r'<h1 class="b-maintitle">(?P<title>.+)</h1>'
    _VALID_URL = r'http://asbook\.net/(?P<section>abooks|radioshow|inyaz)/(?P<subsection>\S+)/(?P<id>\S+).html'
    _TEST = {
        'url': 'http://asbook.net/abooks/fantastic/8904-grad-obrechennyy-boris-i-arkadiy-strugackie.html',
        'md5': 'ab3220ba94ed5bafa7fd796588198862',
        'info_dict': {
            'id': 'Град обреченный - 1',
            'ext': 'mp3',
            'title': '"Град обреченный" Аркадий и Борис Стругацкие',
            'upload_date': '20160216',
        }
    }

    def _real_extract(self, url):
        book_id = self._match_id(url)

        page = self._download_webpage(url, book_id)

        json_url = None
        for mobj in re.finditer(PACKED_CODES_RE, page):
            packed_data = mobj.group(0).replace('\\\'', '\'')
            text = self.decode_packed_codes(packed_data)
            json_url = self._search_regex(r"json_url='(?P<json_url>\S+)';",
                                          text, 'json_url', default=None)
            if json_url is not None:
                break

        if not json_url:
            raise ExtractorError('Could not get information about audiobook',
                                 expected=True)

        title = None
        for mobj in re.finditer(self._VIDEO_RE, page):
            info = mobj.groupdict()
            if 'title' in info:
                title = info['title'].strip()
                break

        playlist = self._download_json(json_url, book_id).get('playlist', None)

        if not title:
            title = playlist[0]['comment']

        return self.playlist_result(self._entries(playlist, title),
                                    book_id, title)

    @staticmethod
    def decode_packed_codes(code):
        # This method copies the method from utils.decode_packed_codes,
        # but it correctly passes Cyrillic characters

        mobj = re.search(PACKED_CODES_RE, code)
        obfucasted_code, base, count, symbols = mobj.groups()
        base = int(base)
        count = int(count)
        symbols = symbols.split('|')
        symbol_table = {}

        while count:
            count -= 1
            base_n_count = encode_base_n(count, base)
            symbol_table[base_n_count] = symbols[count] or base_n_count

        return re.sub(
            r'\b(\w+)\b', lambda mobj: symbol_table.get(mobj.group(0)),
            obfucasted_code)

    def _entries(self, playlist, playlist_title):
        for item in playlist:
            info = {'_type': 'url_transparent',
                    'url': item['file'],
                    'ie_key': None,
                    'id': item['comment'],  # instead filename
                    'title': playlist_title  # item['comment']
                    }

            yield info
