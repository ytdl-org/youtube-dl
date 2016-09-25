# coding: utf-8
from __future__ import unicode_literals

import re

from .turner import TurnerBaseIE
from ..utils import extract_attributes


class TBSIE(TurnerBaseIE):
    _VALID_URL = r'https?://(?:www\.)?(?P<site>tbs|tntdrama)\.com/videos/(?:[^/]+/)+(?P<id>[^/?#]+)\.html'
    _TESTS = [{
        'url': 'http://www.tbs.com/videos/people-of-earth/season-1/extras/2007318/theatrical-trailer.html',
        'md5': '9e61d680e2285066ade7199e6408b2ee',
        'info_dict': {
            'id': '2007318',
            'ext': 'mp4',
            'title': 'Theatrical Trailer',
            'description': 'Catch the latest comedy from TBS, People of Earth, premiering Halloween night--Monday, October 31, at 9/8c.',
        }
    }, {
        'url': 'http://www.tntdrama.com/videos/good-behavior/season-1/extras/1538823/you-better-run.html',
        'md5': 'ce53c6ead5e9f3280b4ad2031a6fab56',
        'info_dict': {
            'id': '1538823',
            'ext': 'mp4',
            'title': 'You Better Run',
            'description': 'Letty Raines must figure out what she\'s running toward while running away from her past. Good Behavior premieres November 15 at 9/8c.',
        }
    }]

    def _real_extract(self, url):
        domain, display_id = re.match(self._VALID_URL, url).groups()
        site = domain[:3]
        webpage = self._download_webpage(url, display_id)
        video_params = extract_attributes(self._search_regex(r'(<[^>]+id="page-video"[^>]*>)', webpage, 'video params'))
        query = None
        clip_id = video_params.get('clipid')
        if clip_id:
            query = 'id=' + clip_id
        else:
            query = 'titleId=' + video_params['titleid']
        return self._extract_cvp_info(
            'http://www.%s.com/service/cvpXml?%s' % (domain, query), display_id, {
                'default': {
                    'media_src': 'http://ht.cdn.turner.com/%s/big' % site,
                },
                'secure': {
                    'media_src': 'http://androidhls-secure.cdn.turner.com/%s/big' % site,
                    'tokenizer_src': 'http://www.%s.com/video/processors/services/token_ipadAdobe.do' % domain,
                },
            }, {
                'url': url,
                'site_name': site.upper(),
                'auth_required': video_params.get('isAuthRequired') != 'false',
            })
