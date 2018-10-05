# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..utils import (
    js_to_json,
    merge_dicts
)


class RaisudtirolIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?raisudtirol\.rai\.it/(?:de|it|la)/index.php\?media\=(?P<id>...[0-9]+)'
    _TESTS = [
        {
            'url': 'http://www.raisudtirol.rai.it/la/index.php?media=Ttv1538690400',
            'md5': 'cb29c5cf2a39f75a055685612260ad95',
            'info_dict': {
                'id': 'Ttv1538690400',
                'ext': 'mp4',
                'title': 'TRAIL 10',
                'thumbnail': r're:^https?://.*\.jpg$',
             },
        }, {
            'url': 'http://www.raisudtirol.rai.it/it/index.php?media=Ptv1538300700',
            'md5': 'aff4a51dc402a19a3effeeeb271ef538',
            'info_dict': {
                'id': 'Ptv1538300700',
                'ext': 'mp4',
                'title': 'Tapis Roulant',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        }, {
             'url': 'http://www.raisudtirol.rai.it/de/index.php?media=Ptv1538511600',
             'md5': '9523207e57a0db6b322eccb70825142a',
             'info_dict': {
                 'id': 'Ptv1538511600',
                 'ext': 'mp4',
                 'title': 'Pro und Contra: Kein Einkaufen am Sonntag mehr?',
                 'thumbnail': r're:^https?://.*\.jpg$',
             }
        }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._html_search_regex(r'<span class="med_title">(.+?)</span>', webpage, 'title', default=video_id, fatal=False)
        info_dict = {
                'id': video_id,
                'title': title,
            }
        jwplayer_data = self._find_jwplayer_data(webpage, video_id, transform_source=js_to_json)
        if jwplayer_data:
            try:
                info = self._parse_jwplayer_data(
                    jwplayer_data, video_id, require_title=False, base_url=url)
                if info['thumbnail']:
                    info['thumbnail'] = ('http://www.raisudtirol.rai.it' + info['thumbnail'])
                return merge_dicts(info, info_dict)
            except ExtractorError:
                # See https://github.com/rg3/youtube-dl/pull/16735
                pass
