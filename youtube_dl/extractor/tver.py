# coding: utf-8
from __future__ import unicode_literals

import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    js_to_json,
)


class TVerIE(InfoExtractor):

    _TEST = {
        'url': 'https://tver.jp/feature/f0057485',  # In addition to 'feature', there are also categories such as 'corner' and 'episode'.
        'md5': '4ae1bc00e6d55af8f7e2b2c17029f1a3',  # MD5 hash of a short video downloaded by running youtube-dl with the --test option
        'info_dict': {
            'id': 'f0057485',  # TVer ID
            'display_id': 'ref:hanzawa_naoki---s2----323-001',  # Brightcove ID
            'ext': 'mp4',
            'title': '半沢直樹(新シリーズ)　第1話 子会社VS銀行!飛ばされた半沢の新たな下剋上が始まる',
            'description': 'md5:92ce839312ee1e9b162de73fa08b6374',
            'thumbnail': r're:https?://.*\.jpg$',
            'duration': 4100.032,
            'timestamp': 1600308623,
            'upload_date': '20200917',
            'uploader_id': '4031511847001',
        },
        'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
    }

    IE_NAME = 'TVer'
    IE_DESC = 'TVer'

    _VALID_URL = r'https?://(?:www\.)?tver\.jp/(corner|episode|feature)/(?P<id>f?[0-9]+)'
    _GEO_COUNTRIES = ['JP']  # TVer service is limited to Japan only

    BRIGHTCOVE_URL_TEMPLATE = 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s'

    # TODO: FOD対応
    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # extract tver information
        tver_info_csv = self._search_regex(r'addPlayer\((?P<tver_info>.*?)\);', webpage, 'tver information', flags=re.DOTALL).strip()
        tver_info_csv = tver_info_csv.replace('\t', '').replace('\n', '').replace('\'', '')  # remove \t and \n and '
        tver_info = tver_info_csv.split(',')

        # extract brightcove information
        brightcove_account_id = tver_info[3]
        brightcove_video_id = 'ref:' + tver_info[4]
        brightcove_url = self.BRIGHTCOVE_URL_TEMPLATE % (brightcove_account_id, brightcove_video_id)
        brightcove_info = self._extract_brightcove_info(brightcove_url, 'https://tver.jp/')

        # extract tver description
        description = \
            self._html_search_meta(['og:description', 'twitter:description'], webpage, 'description', default=None) or \
            self._html_search_regex(r'<div[^>]+class="description"[^>]*>(?P<description>.*?)</div>', webpage, 'description', default=None, flags=re.DOTALL)

        # Note: Delegate extraction to BrightcoveNewIE by specifying url_transparent,
        # while also making TverIE's own acquired entities such as description available.
        info_dict = {
            '_type': 'url_transparent',
            'url': brightcove_url,
            'ie_key': BrightcoveNewIE.ie_key(),
            'id': video_id,  # Tver ID
            'display_id': brightcove_video_id,  # Brightcove ID
            'title': brightcove_info.get('name'),
            'description': description,
            'thumbnail': re.sub(r'/[0-9]+x[0-9]+/', r'/1920x1080/', brightcove_info.get('poster')),  # select large thumbnail
            'creator': tver_info[7],  # Broadcaster name  e.g. 'tbs', 'ntv'
            'uploader': tver_info[8],  # Delivery platform name  e.g. 'TBS FREE', '日テレ無料'
        }

        return info_dict

    def _extract_brightcove_info(self, url, referrer):

        valid_url = r'https?://players\.brightcove\.net/(?P<account_id>\d+)/(?P<player_id>[^/]+)_(?P<embed>[^/]+)/index\.html\?.*(?P<content_type>video|playlist)Id=(?P<video_id>\d+|ref:[^&]+)'

        account_id, player_id, embed, content_type, video_id = re.match(valid_url, url).groups()

        def extract_policy_key():
            webpage = self._download_webpage(
                'http://players.brightcove.net/%s/%s_%s/index.min.js'
                % (account_id, player_id, embed), video_id)

            policy_key = None

            catalog = self._search_regex(
                r'catalog\(({.+?})\);', webpage, 'catalog', default=None)
            if catalog:
                catalog = self._parse_json(
                    js_to_json(catalog), video_id, fatal=False)
                if catalog:
                    policy_key = catalog.get('policyKey')

            if not policy_key:
                policy_key = self._search_regex(
                    r'policyKey\s*:\s*(["\'])(?P<pk>.+?)\1',
                    webpage, 'policy key', group='pk')

            return policy_key

        # brightcove api url
        api_url = 'https://edge.api.brightcove.com/playback/v1/accounts/%s/%ss/%s' % (account_id, content_type, video_id)

        # set header
        headers = {
            'Accept': 'application/json;pk=%s' % extract_policy_key(),
            'Origin': re.search(r'https?://[^/]+', referrer).group(0),
            'Referer': referrer,
        }

        # return brightcove api info
        return self._download_json(api_url, video_id, headers=headers)
