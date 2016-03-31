# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote


class VoxMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:theverge|vox|sbnation|eater|polygon|curbed|racked)\.com/(?:[^/]+/)*(?P<id>[^/?]+)'
    _TESTS = [{
        'url': 'http://www.theverge.com/2014/6/27/5849272/material-world-how-google-discovered-what-software-is-made-of',
        'md5': '73856edf3e89a711e70d5cf7cb280b37',
        'info_dict': {
            'id': '11eXZobjrG8DCSTgrNjVinU-YmmdYjhe',
            'ext': 'mp4',
            'title': 'Google\'s new material design direction',
            'description': 'md5:2f44f74c4d14a1f800ea73e1c6832ad2',
        }
    }, {
        # data-ooyala-id
        'url': 'http://www.theverge.com/2014/10/21/7025853/google-nexus-6-hands-on-photos-video-android-phablet',
        'md5': 'd744484ff127884cd2ba09e3fa604e4b',
        'info_dict': {
            'id': 'RkZXU4cTphOCPDMZg5oEounJyoFI0g-B',
            'ext': 'mp4',
            'title': 'The Nexus 6: hands-on with Google\'s phablet',
            'description': 'md5:87a51fe95ff8cea8b5bdb9ac7ae6a6af',
        }
    }, {
        # volume embed
        'url': 'http://www.vox.com/2016/3/31/11336640/mississippi-lgbt-religious-freedom-bill',
        'md5': '375c483c5080ab8cd85c9c84cfc2d1e4',
        'info_dict': {
            'id': 'wydzk3dDpmRz7PQoXRsTIX6XTkPjYL0b',
            'ext': 'mp4',
            'title': 'The new frontier of LGBTQ civil rights, explained',
            'description': 'md5:0dc58e94a465cbe91d02950f770eb93f',
        }
    }, {
        # youtube embed
        'url': 'http://www.vox.com/2016/3/24/11291692/robot-dance',
        'md5': '83b3080489fb103941e549352d3e0977',
        'info_dict': {
            'id': 'FcNHTJU1ufM',
            'ext': 'mp4',
            'title': 'How "the robot" became the greatest novelty dance of all time',
            'description': 'md5:b081c0d588b8b2085870cda55e6da176',
            'upload_date': '20160324',
            'uploader_id': 'voxdotcom',
            'uploader': 'Vox',
        }
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = compat_urllib_parse_unquote(self._download_webpage(url, display_id))

        title = None
        description = None
        provider_video_id = None
        provider_video_type = None

        entry = self._search_regex([
            r'Chorus\.VideoContext\.addVideo\(\[({.+})\]\);',
            r'var\s+entry\s*=\s*({.+});'
        ], webpage, 'video data', default=None)
        if entry:
            video_data = self._parse_json(entry, display_id)
            provider_video_id = video_data.get('provider_video_id')
            provider_video_type = video_data.get('provider_video_type')
            if provider_video_id and provider_video_type:
                title = video_data.get('title')
                description = video_data.get('description')

        if not provider_video_id or not provider_video_type:
            provider_video_id = self._search_regex(
                r'data-ooyala-id="([^"]+)"', webpage, 'ooyala id', default=None)
            if provider_video_id:
                provider_video_type = 'ooyala'
            else:
                volume_uuid = self._search_regex(r'data-volume-uuid="([^"]+)"', webpage, 'volume uuid')
                volume_webpage = self._download_webpage(
                    'http://volume.vox-cdn.com/embed/%s' % volume_uuid, volume_uuid)
                video_data = self._parse_json(self._search_regex(
                    r'Volume\.createVideo\(({.+})\s*,\s*{.*}\);', volume_webpage, 'video data'), volume_uuid)
                title = video_data.get('title_short')
                description = video_data.get('description_long') or video_data.get('description_short')
                for pvtype in ('ooyala', 'youtube'):
                    provider_video_id = video_data.get('%s_id' % pvtype)
                    if provider_video_id:
                        provider_video_type = pvtype
                        break

        return {
            '_type': 'url_transparent',
            'url': provider_video_id if provider_video_type == 'youtube' else '%s:%s' % (provider_video_type, provider_video_id),
            'title': title or self._og_search_title(webpage),
            'description': description or self._og_search_description(webpage),
        }
