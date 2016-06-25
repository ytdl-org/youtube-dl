# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_str,
    compat_urllib_parse_unquote,
)
from ..utils import (
    int_or_none,
    strip_or_none,
    unified_timestamp,
)


class PolskieRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?polskieradio\.pl/\d+/\d+/Artykul/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.polskieradio.pl/7/5102/Artykul/1587943,Prof-Andrzej-Nowak-o-historii-nie-da-sie-myslec-beznamietnie',
        'info_dict': {
            'id': '1587943',
            'title': 'Prof. Andrzej Nowak: o historii nie da się myśleć beznamiętnie',
            'description': 'md5:12f954edbf3120c5e7075e17bf9fc5c5',
        },
        'playlist': [{
            'md5': '2984ee6ce9046d91fc233bc1a864a09a',
            'info_dict': {
                'id': '1540576',
                'ext': 'mp3',
                'title': 'md5:d4623290d4ac983bf924061c75c23a0d',
                'timestamp': 1456594200,
                'upload_date': '20160227',
                'duration': 2364,
            },
        }],
    }, {
        'url': 'http://www.polskieradio.pl/265/5217/Artykul/1635803,Euro-2016-nie-ma-miejsca-na-blad-Polacy-graja-ze-Szwajcaria-o-cwiercfinal',
        'info_dict': {
            'id': '1635803',
            'title': 'Euro 2016: nie ma miejsca na błąd. Polacy grają ze Szwajcarią o ćwierćfinał',
            'description': 'md5:01cb7d0cad58664095d72b51a1ebada2',
        },
        'playlist_mincount': 12,
    }, {
        'url': 'http://polskieradio.pl/9/305/Artykul/1632955,Bardzo-popularne-slowo-remis',
        'only_matching': True,
    }, {
        'url': 'http://www.polskieradio.pl/7/5102/Artykul/1587943',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        content = self._search_regex(
            r'(?s)<div[^>]+class="audio atarticle"[^>]*>(.+?)<script>',
            webpage, 'content')

        timestamp = unified_timestamp(self._html_search_regex(
            r'(?s)<span[^>]+id="datetime2"[^>]*>(.+?)</span>',
            webpage, 'timestamp', fatal=False))

        entries = []

        media_urls = set()

        for data_media in re.findall(r'<[^>]+data-media=({[^>]+})', content):
            media = self._parse_json(data_media, playlist_id, fatal=False)
            if not media.get('file') or not media.get('desc'):
                continue
            media_url = self._proto_relative_url(media['file'], 'http:')
            if media_url in media_urls:
                continue
            media_urls.add(media_url)
            entries.append({
                'id': compat_str(media['id']),
                'url': media_url,
                'title': compat_urllib_parse_unquote(media['desc']),
                'duration': int_or_none(media.get('length')),
                'vcodec': 'none' if media.get('provider') == 'audio' else None,
                'timestamp': timestamp,
            })

        title = self._og_search_title(webpage).strip()
        description = strip_or_none(self._og_search_description(webpage))

        return self.playlist_result(entries, playlist_id, title, description)
