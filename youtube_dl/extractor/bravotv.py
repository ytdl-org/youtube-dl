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
        'url': 'http://www.bravotv.com/last-chance-kitchen/season-5/videos/lck-ep-12-fishy-finale',
        'md5': '9086d0b7ef0ea2aabc4781d75f4e5863',
        'info_dict': {
            'id': 'zHyk1_HU_mPy',
            'ext': 'mp4',
            'title': 'LCK Ep 12: Fishy Finale',
            'description': 'S13/E12: Two eliminated chefs have just 12 minutes to cook up a delicious fish dish.',
            'uploader': 'NBCU-BRAV',
            'upload_date': '20160302',
            'timestamp': 1456945320,
        }
    }, {
        'url': 'http://www.bravotv.com/below-deck/season-3/ep-14-reunion-part-1',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        settings = self._parse_json(self._search_regex(
            r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);', webpage, 'drupal settings'),
            display_id)
        info = {}
        query = {
            'mbr': 'true',
        }
        account_pid, release_pid = [None] * 2
        tve = settings.get('sharedTVE')
        if tve:
            query['manifest'] = 'm3u'
            account_pid = 'HNK2IC'
            release_pid = tve['release_pid']
            if tve.get('entitlement') == 'auth':
                adobe_pass = settings.get('adobePass', {})
                resource = self._get_mvpd_resource(
                    adobe_pass.get('adobePassResourceId', 'bravo'),
                    tve['title'], release_pid, tve.get('rating'))
                query['auth'] = self._extract_mvpd_auth(
                    url, release_pid, adobe_pass.get('adobePassRequestorId', 'bravo'), resource)
        else:
            shared_playlist = settings['shared_playlist']
            account_pid = shared_playlist['account_pid']
            metadata = shared_playlist['video_metadata'][shared_playlist['default_clip']]
            release_pid = metadata['release_pid']
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
            'url': smuggle_url(update_url_query(
                'http://link.theplatform.com/s/%s/%s' % (account_pid, release_pid),
                query), {'force_smil_url': True}),
            'ie_key': 'ThePlatform',
        })
        return info
