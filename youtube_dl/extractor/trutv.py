# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE


class TruTVIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?trutv\.com(?:(?P<path>/shows/[^/]+/videos/[^/?#]+?)\.html|/full-episodes/[^/]+/(?P<id>\d+))'
    _TEST = {
        'url': 'http://www.trutv.com/shows/10-things/videos/you-wont-believe-these-sports-bets.html',
        'md5': '2cdc844f317579fed1a7251b087ff417',
        'info_dict': {
            'id': '/shows/10-things/videos/you-wont-believe-these-sports-bets',
            'ext': 'mp4',
            'title': 'You Won\'t Believe These Sports Bets',
            'description': 'Jamie Lee sits down with a bookie to discuss the bizarre world of illegal sports betting.',
            'upload_date': '20130305',
        }
    }

    def _real_extract(self, url):
        path, video_id = re.match(self._VALID_URL, url).groups()
        auth_required = False
        if path:
            data_src = 'http://www.trutv.com/video/cvp/v2/xml/content.xml?id=%s.xml' % path
        else:
            webpage = self._download_webpage(url, video_id)
            video_id = self._search_regex(
                r"TTV\.TVE\.episodeId\s*=\s*'([^']+)';",
                webpage, 'video id', default=video_id)
            auth_required = self._search_regex(
                r'TTV\.TVE\.authRequired\s*=\s*(true|false);',
                webpage, 'auth required', default='false') == 'true'
            data_src = 'http://www.trutv.com/tveverywhere/services/cvpXML.do?titleId=' + video_id
        return self._extract_cvp_info(
            data_src, path, {
                'secure': {
                    'media_src': 'http://androidhls-secure.cdn.turner.com/trutv/big',
                    'tokenizer_src': 'http://www.trutv.com/tveverywhere/processors/services/token_ipadAdobe.do',
                },
            }, {
                'url': url,
                'site_name': 'truTV',
                'auth_required': auth_required,
            })
