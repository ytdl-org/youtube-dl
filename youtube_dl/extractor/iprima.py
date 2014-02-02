# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from random import random
from math import floor

from .common import InfoExtractor
from ..utils import compat_urllib_request


class IPrimaIE(InfoExtractor):
    _VALID_URL = r'https?://play\.iprima\.cz/(?P<videogroup>.+)/(?P<videoid>.+)'

    _TESTS = [{
        'url': 'http://play.iprima.cz/particka/particka-92',
        'info_dict': {
            'id': '39152',
            'ext': 'flv',
            'title': 'Partička (92)',
            'description': 'md5:d7ddd08606d17ea524f30306e494847a',
            'thumbnail': 'http://play.iprima.cz/sites/default/files/image_crops/image_620x349/3/491483_particka-92_image_620x349.jpg',
        },
        'params': {
            'skip_download': True,
        },
    },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        webpage = self._download_webpage(url, video_id)

        player_url = 'http://embed.livebox.cz/iprimaplay/player-embed-v2.js?__tok%s__=%s' % (
                         floor(random()*1073741824),
                         floor(random()*1073741824))

        req = compat_urllib_request.Request(player_url)
        req.add_header('Referer', url)
        playerpage = self._download_webpage(req, video_id)

        base_url = ''.join(re.findall(r"embed\['stream'\] = '(.+?)'.+'(\?auth=)'.+'(.+?)';", playerpage)[1])

        zoneGEO = self._html_search_regex(r'"zoneGEO":(.+?),', webpage, 'zoneGEO')

        if zoneGEO != '0':
            base_url = base_url.replace('token', 'token_'+zoneGEO)

        formats = []
        for format_id in ['lq', 'hq', 'hd']:
            filename = self._html_search_regex(r'"%s_id":(.+?),' % format_id, webpage, 'filename')

            if filename == 'null':
                continue

            real_id = self._search_regex(r'Prima-[0-9]{10}-([0-9]+)_', filename, 'real video id')

            if format_id == 'hd':
                filename = 'hq/'+filename

            formats.append({
                'format_id': format_id,
                'url': base_url,
                'play_path': 'mp4:'+filename.replace('"', '')[:-4],
                'rtmp_live': True,
                'ext': 'flv',
                })

        return {
            'id': real_id,
            'title': self._og_search_title(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
        }