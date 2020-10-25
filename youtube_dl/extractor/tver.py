# coding: utf-8
from __future__ import unicode_literals

import re

from .brightcove import BrightcoveNewIE
from .common import InfoExtractor
from ..utils import (
    js_to_json,
)


class TVerIE(InfoExtractor):

    _TESTS = [
        {
            # Delivery from Brightcove
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
                'creator': 'tbs',  # Means TBS TV
                'uploader': 'TBS FREE',  # Content provider
            },
            'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
        },
        {
            # Delivery from FOD (Fuji TV On Demand)
            'url': 'https://tver.jp/corner/f0057932',  # In addition to 'feature', there are also categories such as 'corner' and 'episode'.
            'md5': '6d1970594e532f4b1d6403b5bf9d0d67',  # MD5 hash of a short video downloaded by running youtube-dl with the --test option
            'info_dict': {
                'id': 'f0057932',  # TVer ID
                'display_id': '5d40810015',  # FOD ID
                'ext': 'mp4',
                'title': 'ちびまる子ちゃん　#1258「秋のお楽しみメニュー～まる子の昔ばなし～ 『まる子の涼しい大作戦』の巻／『まる子のおむすびころりん』の巻」',
                'description': 'md5:328c6ef38bed76588a1f6eb5d69c4a7c',
                'thumbnail': r're:https?://.*\.jpg$',
                'creator': 'cx',  # Means Fuji TV
                'uploader': 'FOD見逃し無料',  # Content provider
            },
            'skip': 'Running from test_download.py doesn\'t seem to be able to handle encrypted HLS videos',
        },
    ]

    IE_NAME = 'TVer'
    IE_DESC = 'TVer'

    _VALID_URL = r'https?://(?:www\.)?tver\.jp/(corner|episode|feature)/(?P<id>f?[0-9]+)'
    _GEO_COUNTRIES = ['JP']  # TVer service is limited to Japan only

    def _real_extract(self, url):

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        # extract tver information
        tver_info_csv = self._search_regex(r'addPlayer\((?P<tver_info>.*?)\);', webpage, 'tver information', flags=re.DOTALL).strip()
        tver_info_csv = tver_info_csv.replace('\t', '').replace('\n', '').replace('\'', '')  # remove \t and \n and '
        tver_info = tver_info_csv.split(',')

        # extract tver title
        title = tver_info[5] + '　' + tver_info[6].lstrip()  # title + subtitle

        # extract tver description
        description = \
            self._html_search_meta(['og:description', 'twitter:description'], webpage, 'description', default=None) or \
            self._html_search_regex(r'<div[^>]+class="description"[^>]*>(?P<description>.*?)</div>', webpage, 'description', default=None, flags=re.DOTALL)

        # Note: Of the videos on TVer, only the videos distributed by Fuji TV (FOD, Fuji TV On Demand)
        # use our own distribution system instead of Brightcove.
        if tver_info[7] == 'cx':

            # extract fod information
            fod_video_id = tver_info[3]
            fod_url = 'https://i.fod.fujitv.co.jp/abr/pc_html5/%s.m3u8' % fod_video_id
            fod_thumbnail = 'https://i.fod.fujitv.co.jp/pc/image/wbtn/wbtn_%s.jpg' % fod_video_id

            # extract fod formats
            fod_formats = self._extract_m3u8_formats(fod_url, fod_video_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls')

            # Note: All 'RESOLUTION' values in the playlist are 360p,
            # but this is a fake value and will be replaced based on what you actually downloaded and measured.
            for index, fod_fotmat in enumerate(fod_formats):
                # 720p, 2000kbps
                if fod_fotmat['format_id'] == 'hls-2000':
                    fod_formats[index]['width'] = 1280
                    fod_formats[index]['height'] = 720
                # 720p, 1200kbps
                elif fod_fotmat['format_id'] == 'hls-1200':
                    fod_formats[index]['width'] = 1280
                    fod_formats[index]['height'] = 720
                # 360p, 800kbps
                elif fod_fotmat['format_id'] == 'hls-800':
                    fod_formats[index]['width'] = 640
                    fod_formats[index]['height'] = 360
                # 180p, 300kbps
                elif fod_fotmat['format_id'] == 'hls-300':
                    fod_formats[index]['width'] = 320
                    fod_formats[index]['height'] = 180

            # reverse the format order
            fod_formats.reverse()

            info_dict = {
                'id': video_id,  # TVer ID
                'display_id': fod_video_id,  # FOD ID
                'formats': fod_formats,
                'title': title,
                'description': description,
                'thumbnail': fod_thumbnail,
                'creator': tver_info[7],  # Broadcaster name  e.g. 'cx'
                'uploader': tver_info[8],  # Delivery platform name  e.g. 'FOD見逃し無料'
                'tags': [tver_info[5]],
                'is_live': False,
            }

        else:

            # extract brightcove information
            brightcove_account_id = tver_info[3]
            brightcove_video_id = 'ref:' + tver_info[4]
            brightcove_url = 'http://players.brightcove.net/%s/default_default/index.html?videoId=%s' % (brightcove_account_id, brightcove_video_id)
            brightcove_info = self._extract_brightcove_info(brightcove_url, 'https://tver.jp/')

            # Note: Delegate extraction to BrightcoveNewIE by specifying url_transparent,
            # while also making TVerIE's own acquired entities such as description available.
            info_dict = {
                '_type': 'url_transparent',
                'url': brightcove_url,
                'ie_key': BrightcoveNewIE.ie_key(),
                'id': video_id,  # TVer ID
                'display_id': brightcove_video_id,  # Brightcove ID
                'title': title or brightcove_info.get('name'),
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
