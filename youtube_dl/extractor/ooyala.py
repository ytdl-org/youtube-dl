from __future__ import unicode_literals
import re
import json

from .common import InfoExtractor
from ..utils import unescapeHTML


class OoyalaIE(InfoExtractor):
    _VALID_URL = r'https?://.+?\.ooyala\.com/.*?(?:embedCode|ec)=(?P<id>.+?)(&|$)'

    _TEST = {
        # From http://it.slashdot.org/story/13/04/25/178216/recovering-data-from-broken-hard-drives-and-ssds-video
        'url': 'http://player.ooyala.com/player.js?embedCode=pxczE2YjpfHfn1f3M-ykG_AmJRRn0PD8',
        'md5': '3f5cceb3a7bf461d6c29dc466cf8033c',
        'info_dict': {
            'id': 'pxczE2YjpfHfn1f3M-ykG_AmJRRn0PD8',
            'ext': 'mp4',
            'title': 'Explaining Data Recovery from Hard Drives and SSDs',
            'description': 'How badly damaged does a drive have to be to defeat Russell and his crew? Apparently, smashed to bits.',
        },
    }

    @staticmethod
    def _url_for_embed_code(embed_code):
        return 'http://player.ooyala.com/player.js?embedCode=%s' % embed_code

    @classmethod
    def _build_url_result(cls, embed_code):
        return cls.url_result(cls._url_for_embed_code(embed_code),
            ie=cls.ie_key())

    def _extract_result(self, info, more_info):
        return {
            'id': info['embedCode'],
            'ext': 'mp4',
            'title': unescapeHTML(info['title']),
            'url': info.get('ipad_url') or info['url'],
            'description': unescapeHTML(more_info['description']),
            'thumbnail': more_info['promo'],
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        embedCode = mobj.group('id')
        player_url = 'http://player.ooyala.com/player.js?embedCode=%s' % embedCode
        player = self._download_webpage(player_url, embedCode)
        mobile_url = self._search_regex(r'mobile_player_url="(.+?)&device="',
                                        player, 'mobile player url')
        mobile_player = self._download_webpage(mobile_url, embedCode)
        videos_info = self._search_regex(
            r'var streams=window.oo_testEnv\?\[\]:eval\("\((\[{.*?}\])\)"\);',
            mobile_player, 'info').replace('\\"','"')
        videos_more_info = self._search_regex(r'eval\("\(({.*?\\"promo\\".*?})\)"', mobile_player, 'more info').replace('\\"','"')
        videos_info = json.loads(videos_info)
        videos_more_info =json.loads(videos_more_info)

        if videos_more_info.get('lineup'):
            videos = [self._extract_result(info, more_info) for (info, more_info) in zip(videos_info, videos_more_info['lineup'])]
            return {
                '_type': 'playlist',
                'id': embedCode,
                'title': unescapeHTML(videos_more_info['title']),
                'entries': videos,
            }
        else:
            return self._extract_result(videos_info[0], videos_more_info)
        
