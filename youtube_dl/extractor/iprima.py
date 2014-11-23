# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from random import random
from math import floor

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    ExtractorError,
)


class IPrimaIE(InfoExtractor):
    _VALID_URL = r'https?://play\.iprima\.cz/[^?#]+/(?P<id>[^?#]+)'

    _TESTS = [{
        'url': 'http://play.iprima.cz/particka/particka-92',
        'info_dict': {
            'id': '39152',
            'ext': 'flv',
            'title': 'Partička (92)',
            'description': 'md5:3740fda51464da35a2d4d0670b8e4fd6',
            'thumbnail': 'http://play.iprima.cz/sites/default/files/image_crops/image_620x349/3/491483_particka-92_image_620x349.jpg',
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
    }, {
        'url': 'http://play.iprima.cz/particka/tchibo-particka-jarni-moda',
        'info_dict': {
            'id': '9718337',
            'ext': 'flv',
            'title': 'Tchibo Partička - Jarní móda',
            'description': 'md5:589f8f59f414220621ff8882eb3ce7be',
            'thumbnail': 're:^http:.*\.jpg$',
        },
        'params': {
            'skip_download': True,  # requires rtmpdump
        },
        'skip': 'Do not have permission to access this page',
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        if re.search(r'Nemáte oprávnění přistupovat na tuto stránku\.\s*</div>', webpage):
            raise ExtractorError(
                '%s said: You do not have permission to access this page' % self.IE_NAME, expected=True)

        player_url = (
            'http://embed.livebox.cz/iprimaplay/player-embed-v2.js?__tok%s__=%s' %
            (floor(random() * 1073741824), floor(random() * 1073741824))
        )

        req = compat_urllib_request.Request(player_url)
        req.add_header('Referer', url)
        playerpage = self._download_webpage(req, video_id)

        base_url = ''.join(re.findall(r"embed\['stream'\] = '(.+?)'.+'(\?auth=)'.+'(.+?)';", playerpage)[1])

        zoneGEO = self._html_search_regex(r'"zoneGEO":(.+?),', webpage, 'zoneGEO')
        if zoneGEO != '0':
            base_url = base_url.replace('token', 'token_' + zoneGEO)

        formats = []
        for format_id in ['lq', 'hq', 'hd']:
            filename = self._html_search_regex(
                r'"%s_id":(.+?),' % format_id, webpage, 'filename')

            if filename == 'null':
                continue

            real_id = self._search_regex(
                r'Prima-(?:[0-9]{10}|WEB)-([0-9]+)[-_]',
                filename, 'real video id')

            if format_id == 'lq':
                quality = 0
            elif format_id == 'hq':
                quality = 1
            elif format_id == 'hd':
                quality = 2
                filename = 'hq/' + filename

            formats.append({
                'format_id': format_id,
                'url': base_url,
                'quality': quality,
                'play_path': 'mp4:' + filename.replace('"', '')[:-4],
                'rtmp_live': True,
                'ext': 'flv',
            })

        self._sort_formats(formats)

        return {
            'id': real_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }
