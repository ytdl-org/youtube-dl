# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import int_or_none


class GameInformerIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gameinformer\.com/(?:[^/]+/)*(?P<id>.+)\.aspx'
    _TEST = {
        'url': 'http://www.gameinformer.com/b/features/archive/2015/09/26/replay-animal-crossing.aspx',
        'info_dict': {
            'id': '4515472681001',
            'ext': 'm3u8',
            'title': 'Replay - Animal Crossing',
            'description': 'md5:2e211891b215c85d061adc7a4dd2d930',
            'timestamp': 1443457610706,
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        bc_api_url = self._search_regex(r"getVideo\('([^']+)'", webpage, 'brightcove api url')
        json_data = self._download_json(
            bc_api_url + '&video_fields=id,name,shortDescription,publishedDate,videoStillURL,length,IOSRenditions',
            display_id)

        return {
            'id': compat_str(json_data['id']),
            'display_id': display_id,
            'url': json_data['IOSRenditions'][0]['url'],
            'title': json_data['name'],
            'description': json_data.get('shortDescription'),
            'timestamp': int_or_none(json_data.get('publishedDate')),
            'duration': int_or_none(json_data.get('length')),
        }
