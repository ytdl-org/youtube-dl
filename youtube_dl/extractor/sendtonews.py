# coding: utf-8
from __future__ import unicode_literals

import re

from .jwplatform import JWPlatformBaseIE
from ..compat import compat_parse_qs
from ..utils import (
    ExtractorError,
    parse_duration,
)


class SendtoNewsIE(JWPlatformBaseIE):
    _VALID_URL = r'https?://embed\.sendtonews\.com/player/embed\.php\?(?P<query>[^#]+)'

    _TEST = {
        # From http://cleveland.cbslocal.com/2016/05/16/indians-score-season-high-15-runs-in-blowout-win-over-reds-rapid-reaction/
        'url': 'http://embed.sendtonews.com/player/embed.php?SK=GxfCe0Zo7D&MK=175909&PK=5588&autoplay=on&sound=yes',
        'info_dict': {
            'id': 'GxfCe0Zo7D-175909-5588',
            'ext': 'mp4',
            'title': 'Recap: CLE 15, CIN 6',
            'description': '5/16/16: Indians\' bats explode for 15 runs in a win',
            'duration': 49,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    _URL_TEMPLATE = '//embed.sendtonews.com/player/embed.php?SK=%s&MK=%s&PK=%s'

    @classmethod
    def _extract_url(cls, webpage):
        mobj = re.search(r'''(?x)<script[^>]+src=([\'"])
            (?:https?:)?//embed\.sendtonews\.com/player/responsiveembed\.php\?
                .*\bSC=(?P<SC>[0-9a-zA-Z-]+).*
            \1>''', webpage)
        if mobj:
            sk, mk, pk = mobj.group('SC').split('-')
            return cls._URL_TEMPLATE % (sk, mk, pk)

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        params = compat_parse_qs(mobj.group('query'))

        if 'SK' not in params or 'MK' not in params or 'PK' not in params:
            raise ExtractorError('Invalid URL', expected=True)

        video_id = '-'.join([params['SK'][0], params['MK'][0], params['PK'][0]])

        webpage = self._download_webpage(url, video_id)

        jwplayer_data_str = self._search_regex(
            r'jwplayer\("[^"]+"\)\.setup\((.+?)\);', webpage, 'JWPlayer data')
        js_vars = {
            'w': 1024,
            'h': 768,
            'modeVar': 'html5',
        }
        for name, val in js_vars.items():
            js_val = '%d' % val if isinstance(val, int) else '"%s"' % val
            jwplayer_data_str = jwplayer_data_str.replace(':%s,' % name, ':%s,' % js_val)

        info_dict = self._parse_jwplayer_data(
            self._parse_json(jwplayer_data_str, video_id),
            video_id, require_title=False, rtmp_params={'no_resume': True})

        title = self._html_search_regex(
            r'<div[^>]+class="embedTitle">([^<]+)</div>', webpage, 'title')
        description = self._html_search_regex(
            r'<div[^>]+class="embedSubTitle">([^<]+)</div>', webpage,
            'description', fatal=False)
        duration = parse_duration(self._html_search_regex(
            r'<div[^>]+class="embedDetails">([0-9:]+)', webpage,
            'duration', fatal=False))

        info_dict.update({
            'title': title,
            'description': description,
            'duration': duration,
        })

        return info_dict
