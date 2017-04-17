# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    smuggle_url,
    update_url_query,
)


class FOXIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?fox\.com/watch/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://www.fox.com/watch/255180355939/7684182528',
        'md5': 'ebd296fcc41dd4b19f8115d8461a3165',
        'info_dict': {
            'id': '255180355939',
            'ext': 'mp4',
            'title': 'Official Trailer: Gotham',
            'description': 'Tracing the rise of the great DC Comics Super-Villains and vigilantes, Gotham reveals an entirely new chapter that has never been told.',
            'duration': 129,
            'timestamp': 1400020798,
            'upload_date': '20140513',
            'uploader': 'NEWA-FNG-FOXCOM',
        },
        'add_ie': ['ThePlatform'],
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        settings = self._parse_json(self._search_regex(
            r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
            webpage, 'drupal settings'), video_id)
        fox_pdk_player = settings['fox_pdk_player']
        release_url = fox_pdk_player['release_url']
        query = {
            'mbr': 'true',
            'switch': 'http'
        }
        if fox_pdk_player.get('access') == 'locked':
            ap_p = settings['foxAdobePassProvider']
            rating = ap_p.get('videoRating')
            if rating == 'n/a':
                rating = None
            resource = self._get_mvpd_resource('fbc-fox', None, ap_p['videoGUID'], rating)
            query['auth'] = self._extract_mvpd_auth(url, video_id, 'fbc-fox', resource)

        info = self._search_json_ld(webpage, video_id, fatal=False)
        info.update({
            '_type': 'url_transparent',
            'ie_key': 'ThePlatform',
            'url': smuggle_url(update_url_query(release_url, query), {'force_smil_url': True}),
            'id': video_id,
        })

        return info
