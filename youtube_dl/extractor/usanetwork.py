# coding: utf-8
from __future__ import unicode_literals

from .adobepass import AdobePassIE
from ..utils import (
    NO_DEFAULT,
    smuggle_url,
    update_url_query,
)


class USANetworkIE(AdobePassIE):
    _VALID_URL = r'https?://(?:www\.)?usanetwork\.com/(?:[^/]+/videos|movies)/(?P<id>[^/?#]+)'
    _TEST = {
        'url': 'http://www.usanetwork.com/mrrobot/videos/hpe-cybersecurity',
        'md5': '33c0d2ba381571b414024440d08d57fd',
        'info_dict': {
            'id': '3086229',
            'ext': 'mp4',
            'title': 'HPE Cybersecurity',
            'description': 'The more we digitize our world, the more vulnerable we are.',
            'upload_date': '20160818',
            'timestamp': 1471535460,
            'uploader': 'NBCU-USA',
        },
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        def _x(name, default=NO_DEFAULT):
            return self._search_regex(
                r'data-%s\s*=\s*(["\'])(?P<value>(?:(?!\1).)+)\1' % name,
                webpage, name, default=default, group='value')

        video_id = _x('mpx-guid')
        title = _x('episode-title')
        mpx_account_id = _x('mpx-account-id', '2304992029')

        query = {
            'mbr': 'true',
        }
        if _x('is-full-episode', None) == '1':
            query['manifest'] = 'm3u'

        if _x('is-entitlement', None) == '1':
            adobe_pass = {}
            drupal_settings = self._search_regex(
                r'jQuery\.extend\(Drupal\.settings\s*,\s*({.+?})\);',
                webpage, 'drupal settings', fatal=False)
            if drupal_settings:
                drupal_settings = self._parse_json(drupal_settings, video_id, fatal=False)
                if drupal_settings:
                    adobe_pass = drupal_settings.get('adobePass', {})
            resource = self._get_mvpd_resource(
                adobe_pass.get('adobePassResourceId', 'usa'),
                title, video_id, _x('episode-rating', 'TV-14'))
            query['auth'] = self._extract_mvpd_auth(
                url, video_id, adobe_pass.get('adobePassRequestorId', 'usa'), resource)

        info = self._search_json_ld(webpage, video_id, default={})
        info.update({
            '_type': 'url_transparent',
            'url': smuggle_url(update_url_query(
                'http://link.theplatform.com/s/HNK2IC/media/guid/%s/%s' % (mpx_account_id, video_id),
                query), {'force_smil_url': True}),
            'id': video_id,
            'title': title,
            'series': _x('show-title', None),
            'episode': title,
            'ie_key': 'ThePlatform',
        })
        return info
