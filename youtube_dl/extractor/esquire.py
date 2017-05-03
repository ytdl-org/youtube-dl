# coding: utf-8
from __future__ import unicode_literals

import re

from .adobepass import AdobePassIE
from ..utils import (
    extract_attributes,
    smuggle_url,
    update_url_query,
)


class EsquireIE(AdobePassIE):
    _VALID_URL = r'https?://tv\.esquire\.com/now/(?:[^/]+)/?(?:full-episode)?/(?P<title>[^/?#]+)/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'http://tv.esquire.com/now/team-ninja-warrior/full-episode/finals-week-1/631550531649',
        'md5': '436ee8095d7179704cf2738994d36a20',
        'info_dict': {
            'id': '631550531649',
            'ext': 'mp4',
            'title': 'Finals Week 1',
            'description': 'The first finals episode features the winners of 3 qualifying episodes.',
            'upload_date': '20160301',
            'timestamp': 1456808400,
            'uploader': 'NBCU-MPAT',
        }
    }, {
        'url': 'http://tv.esquire.com/now/friday-night-tykes/full-episode/if-you-wanna-show…/903098435679',
        'md5': 'f1bf3f934ad55424d8c9333a4ab5d3aa',
        'info_dict': {
            'id': '903098435679',
            'ext': 'mp4',
            'title': 'If You Wanna Show\u2026',
            'description': 'On the season Finale of Friday Night Tykes, two champions will be crowned.',
            'upload_date': '20170321',
            'timestamp': 1490068800,
            'uploader': 'NBCU-MPAT',
        }
    }, {
        'url': 'http://tv.esquire.com/now/full-episode/ninja-warrior-402/759415363504',
        'md5': '98a7e5cf805a8a9ebe436345a1bbeb58',
        'info_dict': {
            'id': '759415363504',
            'ext': 'mp4',
            'title': 'Ninja Warrior 402',
            'description': 'Sasuke 4 (Pt. 2) Athletes compete the ultimate obstacle course.',
            'uploader': 'NBCU-MPAT',
            'timestamp': 1472875200,
            'upload_date': '20160903',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        player_params = extract_attributes(self._search_regex(
            r'(<section[^>]+data-tve-page-authz-player-container[^>]*>)', webpage, 'player params'))
        video_id = player_params['data-mpx-id']
        title = player_params['data-episode-title']

        account_pid, path = re.search(
            r'data-src=\"(?:https?)?//player\.theplatform\.com/p/([^/]+)/.*?/embed/select/([\S]+)\"',
            webpage).groups()

        query = {
            'mbr': 'true',
            'manifest': 'm3u'
        }

        if player_params.get('data-entitlement') == 'auth':
            adobe_pass = {}
            drupal_settings = self._search_regex(
                r'Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'drupal settings', fatal=False)
            if drupal_settings:
                drupal_settings = self._parse_json(drupal_settings, video_id, fatal=False)
                if drupal_settings:
                    adobe_pass = drupal_settings.get('adobePass', {})
            resource = self._get_mvpd_resource(
                adobe_pass.get('adobePassResourceId', 'esquire'),
                title, video_id, player_params.get('data-episode-rating', 'TV-14'))
            query['auth'] = self._extract_mvpd_auth(
                url, video_id, adobe_pass.get('adobePassRequestorId', 'esquire'), resource)

        info = self._search_json_ld(webpage, video_id, default={})
        info.update({
            '_type': 'url_transparent',
            'url': smuggle_url(update_url_query(
                'http://link.theplatform.com/s/%s/%s' % (account_pid, path),
                query), {'force_smil_url': True}),
            'id': video_id,
            'title': title,
            'episode': title,
            'ie_key': 'ThePlatform',
        })
        return info
