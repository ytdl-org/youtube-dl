# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    js_to_json,
    smuggle_url,
)


class HGTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?hgtv\.ca/[^/]+/video/(?P<id>[^/]+)/video.html'
    _TEST = {
        'url': 'http://www.hgtv.ca/homefree/video/overnight-success/video.html?v=738081859718&p=1&s=da#video',
        'md5': '',
        'info_dict': {
            'id': 'aFH__I_5FBOX',
            'ext': 'mp4',
            'title': 'Overnight Success',
            'description': 'After weeks of hard work, high stakes, breakdowns and pep talks, the final 2 contestants compete to win the ultimate dream.',
            'uploader': 'SHWM-NEW',
            'timestamp': 1470320034,
            'upload_date': '20160804',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        embed_vars = self._parse_json(self._search_regex(
            r'(?s)embed_vars\s*=\s*({.*?});',
            webpage, 'embed vars'), display_id, js_to_json)
        return {
            '_type': 'url_transparent',
            'url': smuggle_url(
                'http://link.theplatform.com/s/dtjsEC/%s?mbr=true&manifest=m3u' % embed_vars['pid'], {
                    'force_smil_url': True
                }),
            'series': embed_vars.get('show'),
            'season_number': int_or_none(embed_vars.get('season')),
            'episode_number': int_or_none(embed_vars.get('episode')),
            'ie_key': 'ThePlatform',
        }
