# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class GazetaIE(InfoExtractor):
    _VALID_URL = r'(?P<url>https?://(?:www\.)?gazeta\.ru/(?:[^/]+/)?video/(?:(?:main|\d{4}/\d{2}/\d{2})/)?(?P<id>[A-Za-z0-9-_.]+)\.s?html)'
    _TESTS = [{
        'url': 'http://www.gazeta.ru/video/main/zadaite_vopros_vladislavu_yurevichu.shtml',
        'md5': 'd49c9bdc6e5a7888f27475dc215ee789',
        'info_dict': {
            'id': '205566',
            'ext': 'mp4',
            'title': '«70–80 процентов гражданских в Донецке на грани голода»',
            'description': 'md5:38617526050bd17b234728e7f9620a71',
            'thumbnail': 're:^https?://.*\.jpg',
        },
    }, {
        'url': 'http://www.gazeta.ru/lifestyle/video/2015/03/08/master-klass_krasivoi_byt._delaem_vesennii_makiyazh.shtml',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        display_id = mobj.group('id')
        embed_url = '%s?p=embed' % mobj.group('url')
        embed_page = self._download_webpage(
            embed_url, display_id, 'Downloading embed page')

        video_id = self._search_regex(
            r'<div[^>]*?class="eagleplayer"[^>]*?data-id="([^"]+)"', embed_page, 'video id')

        return self.url_result(
            'eagleplatform:gazeta.media.eagleplatform.com:%s' % video_id, 'EaglePlatform')
