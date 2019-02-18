# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    smuggle_url,
    update_url_query,
    int_or_none,
)


class BravoTVIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?bravotv\.com/(?:[^/]+/)+(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://www.bravotv.com/the-real-housewives-of-beverly-hills/season-9/episode-1/videos/lisa-rinna-thinks-denise-richards',
        'md5': 'f8098a7c034fcb1b52ec8b3631803589',
        'info_dict': {
            'id': 'PPhoit2pxdh0',
            'ext': 'mp4',
            'title': 'Lisa Rinna Thinks Denise Richards Will Fit in Well With This Group',
            'description': 'Denise goes back a long way with Rinna, and now the other ladies have a chance to meet her.',
            'uploader': 'NBCU-BRAV',
            'upload_date': '20190204',
            'timestamp': 1549302120,
        }
    }, {
        'url': 'http://www.bravotv.com/below-deck/season-3/ep-14-reunion-part-1',
        'only_matching': True,
    }, {
        'url': 'https://www.bravotv.com/top-chef/season-16/episode-11/videos/lck-ep-12-the-final-knockout',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        settings = self._parse_json(self._search_regex(
            r'<script[^>]+?data-drupal-selector="drupal-settings-json"[^>]*?>({.+?})</script>', webpage, 'drupal settings'),
            display_id)
        info = {}
        query = {
            'mbr': 'true',
        }
        account_pid, release_pid = [None] * 2
        tve = settings.get('ls_tve')
        if tve:
            query['manifest'] = 'm3u'
            account_pid = 'HNK2IC'
            release_pid = tve['release_pid']
            if tve.get('entitlement') == 'auth':
                adobe_pass = settings.get('tve_adobe_auth', {})
                resource = self._get_mvpd_resource(
                    adobe_pass.get('adobePassResourceId', 'bravo'),
                    tve['title'], release_pid, tve.get('rating'))
                query['auth'] = self._extract_mvpd_auth(
                    url, release_pid, adobe_pass.get('adobePassRequestorId', 'bravo'), resource)
            url = smuggle_url(update_url_query(
                'http://link.theplatform.com/s/%s/media/%s' % (account_pid, release_pid),
                query), {'force_smil_url': True})
        else:
            ls_playlist = settings['ls_playlist']
            account_pid = ls_playlist['account_pid']
            metadata = ls_playlist['video_metadata'][ls_playlist['default_clip']]
            release_pid = metadata['release_pid']
            if release_pid:
                url = smuggle_url(update_url_query(
                    'http://link.theplatform.com/s/%s/media/%s' % (account_pid, release_pid),
                    query), {'force_smil_url': True})
            else:
                url = ls_playlist['player_base_url']
            info.update({
                'title': metadata['title'],
                'description': metadata.get('description'),
                'season_number': int_or_none(metadata.get('season_num')),
                'episode_number': int_or_none(metadata.get('episode_num')),
            })
            query['switch'] = 'progressive'
        info.update({
            '_type': 'url_transparent',
            'id': release_pid,
            'url': url,
            'ie_key': 'ThePlatform',
        })
        return info
