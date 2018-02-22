# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_duration,
    try_get,
)


class NexxIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                        (?:
                            https?://api\.nexx(?:\.cloud|cdn\.com)/v3/(?P<domain_id>\d+)/videos/byid/|
                            nexx:(?P<domain_id_s>\d+):
                        )
                        (?P<id>\d+)
                    '''
    _TESTS = [{
        # movie
        'url': 'https://api.nexx.cloud/v3/748/videos/byid/128907',
        'md5': '828cea195be04e66057b846288295ba1',
        'info_dict': {
            'id': '128907',
            'ext': 'mp4',
            'title': 'Stiftung Warentest',
            'alt_title': 'Wie ein Test abläuft',
            'description': 'md5:d1ddb1ef63de721132abd38639cc2fd2',
            'release_year': 2013,
            'creator': 'SPIEGEL TV',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2509,
            'timestamp': 1384264416,
            'upload_date': '20131112',
        },
    }, {
        # episode
        'url': 'https://api.nexx.cloud/v3/741/videos/byid/247858',
        'info_dict': {
            'id': '247858',
            'ext': 'mp4',
            'title': 'Return of the Golden Child (OV)',
            'description': 'md5:5d969537509a92b733de21bae249dc63',
            'release_year': 2017,
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 1397,
            'timestamp': 1495033267,
            'upload_date': '20170517',
            'episode_number': 2,
            'season_number': 2,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://api.nexxcdn.com/v3/748/videos/byid/128907',
        'only_matching': True,
    }, {
        'url': 'nexx:748:128907',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_domain_id(webpage):
        mobj = re.search(
            r'<script\b[^>]+\bsrc=["\'](?:https?:)?//require\.nexx(?:\.cloud|cdn\.com)/(?P<id>\d+)',
            webpage)
        return mobj.group('id') if mobj else None

    @staticmethod
    def _extract_urls(webpage):
        # Reference:
        # 1. https://nx-s.akamaized.net/files/201510/44.pdf

        entries = []

        # JavaScript Integration
        domain_id = NexxIE._extract_domain_id(webpage)
        if domain_id:
            for video_id in re.findall(
                    r'(?is)onPLAYReady.+?_play\.init\s*\(.+?\s*,\s*["\']?(\d+)',
                    webpage):
                entries.append(
                    'https://api.nexx.cloud/v3/%s/videos/byid/%s'
                    % (domain_id, video_id))

        # TODO: support more embed formats

        return entries

    @staticmethod
    def _extract_url(webpage):
        return NexxIE._extract_urls(webpage)[0]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            'https://arc.nexx.cloud/api/video/%s.json' % video_id,
            video_id)['result']

        general = video['general']
        title = general['title']

        stream_data = video['streamdata']
        language = general.get('language_raw') or ''

        # TODO: reverse more cdns

        cdn = stream_data['cdnType']
        assert cdn == 'azure'

        azure_locator = stream_data['azureLocator']

        AZURE_URL = 'http://nx%s%02d.akamaized.net/'

        def get_cdn_shield_base(shield_type='', prefix='-p'):
            for secure in ('', 's'):
                cdn_shield = stream_data.get('cdnShield%sHTTP%s' % (shield_type, secure.upper()))
                if cdn_shield:
                    return 'http%s://%s' % (secure, cdn_shield)
            else:
                return AZURE_URL % (prefix, int(stream_data['azureAccount'].replace('nexxplayplus', '')))

        azure_stream_base = get_cdn_shield_base()
        is_ml = ',' in language
        azure_manifest_url = '%s%s/%s_src%s.ism/Manifest' % (
            azure_stream_base, azure_locator, video_id, ('_manifest' if is_ml else '')) + '%s'

        protection_token = try_get(
            video, lambda x: x['protectiondata']['token'], compat_str)
        if protection_token:
            azure_manifest_url += '?hdnts=%s' % protection_token

        formats = self._extract_m3u8_formats(
            azure_manifest_url % '(format=m3u8-aapl)',
            video_id, 'mp4', 'm3u8_native',
            m3u8_id='%s-hls' % cdn, fatal=False)
        formats.extend(self._extract_mpd_formats(
            azure_manifest_url % '(format=mpd-time-csf)',
            video_id, mpd_id='%s-dash' % cdn, fatal=False))
        formats.extend(self._extract_ism_formats(
            azure_manifest_url % '', video_id, ism_id='%s-mss' % cdn, fatal=False))

        azure_progressive_base = get_cdn_shield_base('Prog', '-d')
        azure_file_distribution = stream_data.get('azureFileDistribution')
        if azure_file_distribution:
            fds = azure_file_distribution.split(',')
            if fds:
                for fd in fds:
                    ss = fd.split(':')
                    if len(ss) == 2:
                        tbr = int_or_none(ss[0])
                        if tbr:
                            f = {
                                'url': '%s%s/%s_src_%s_%d.mp4' % (
                                    azure_progressive_base, azure_locator, video_id, ss[1], tbr),
                                'format_id': '%s-http-%d' % (cdn, tbr),
                                'tbr': tbr,
                            }
                            width_height = ss[1].split('x')
                            if len(width_height) == 2:
                                f.update({
                                    'width': int_or_none(width_height[0]),
                                    'height': int_or_none(width_height[1]),
                                })
                            formats.append(f)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'alt_title': general.get('subtitle'),
            'description': general.get('description'),
            'release_year': int_or_none(general.get('year')),
            'creator': general.get('studio') or general.get('studio_adref'),
            'thumbnail': try_get(
                video, lambda x: x['imagedata']['thumb'], compat_str),
            'duration': parse_duration(general.get('runtime')),
            'timestamp': int_or_none(general.get('uploaded')),
            'episode_number': int_or_none(try_get(
                video, lambda x: x['episodedata']['episode'])),
            'season_number': int_or_none(try_get(
                video, lambda x: x['episodedata']['season'])),
            'formats': formats,
        }


class NexxEmbedIE(InfoExtractor):
    _VALID_URL = r'https?://embed\.nexx(?:\.cloud|cdn\.com)/\d+/(?P<id>[^/?#&]+)'
    _TEST = {
        'url': 'http://embed.nexx.cloud/748/KC1614647Z27Y7T?autoplay=1',
        'md5': '16746bfc28c42049492385c989b26c4a',
        'info_dict': {
            'id': '161464',
            'ext': 'mp4',
            'title': 'Nervenkitzel Achterbahn',
            'alt_title': 'Karussellbauer in Deutschland',
            'description': 'md5:ffe7b1cc59a01f585e0569949aef73cc',
            'release_year': 2005,
            'creator': 'SPIEGEL TV',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 2761,
            'timestamp': 1394021479,
            'upload_date': '20140305',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }

    @staticmethod
    def _extract_urls(webpage):
        # Reference:
        # 1. https://nx-s.akamaized.net/files/201510/44.pdf

        # iFrame Embed Integration
        return [mobj.group('url') for mobj in re.finditer(
            r'<iframe[^>]+\bsrc=(["\'])(?P<url>(?:https?:)?//embed\.nexx(?:\.cloud|cdn\.com)/\d+/(?:(?!\1).)+)\1',
            webpage)]

    def _real_extract(self, url):
        embed_id = self._match_id(url)

        webpage = self._download_webpage(url, embed_id)

        return self.url_result(NexxIE._extract_url(webpage), ie=NexxIE.ie_key())
