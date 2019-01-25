from __future__ import unicode_literals

import base64
import json
import random
import re

from .common import InfoExtractor
from ..compat import compat_parse_qs, compat_b64decode
from ..utils import urljoin, ExtractorError


class VdoCipherIE(InfoExtractor):
    _VALID_URL = r'https?://(?:cdn-[a-z0-9]+\.vdocipher\.com|[a-z0-9]+\.cloudfront\.net)/playerAssets/[0-9\.]+/vdo/embed/index\.html#(?P<querystring>[a-zA-Z0-9&=]+)'
    _TESTS = [{
        'url': 'https://d1z78r8i505acl.cloudfront.net/playerAssets/1.4.7/vdo/embed/index.html#otp=20160313versASE313AYhObv4IOA32eG6QbevHoAuOXxFnLOHsVG12HQdM8dDyVp&playbackInfo=eyJ2aWRlb0lkIjoiNmYxYjY3YmUxNTQ4NDc2M2E4YzM4YTUxZDBkNmQ1OGQifQ==',
        'info_dict': {
            'otp': '20160313versASE313AYhObv4IOA32eG6QbevHoAuOXxFnLOHsVG12HQdM8dDyVp',
            'id': '6f1b67be15484763a8c38a51d0d6d58d',
            'ext': 'mp4',
            'title': "Upload embed demo new.mp4",
            'description': None,
            'duration': 173,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        qs = compat_parse_qs(mobj.group('querystring'))
        otp = qs['otp'][0]
        json_data = compat_b64decode(qs['playbackInfo'][0])
        video_id = json.loads(json_data)['videoId']
        rand = '%d' % (random.random() * 100000)
        data = self._download_json(
            'https://dev.vdocipher.com/api/meta/%s' % video_id, video_id,
            note="Downloading meta manifest")
        hostname = data['hostnames'][0]
        data = self._download_webpage('https://%s/a/' % hostname,
                                      video_id,
                                      note="Downloading metadata",
                                      query={'o': otp, 'p': 'hls', 'ran': rand})
        meta = json.loads(compat_b64decode(data))
        m3u8_url = meta['url']
        m3u8_content = self._download_webpage(
            m3u8_url, video_id, note="Downloading m3u8 for the key")

        # YTD does not load the cookies for the url of the key, it reuses the cookies obtained for the m3u8.
        # In our cases these cookies are different from the ones used by the key, so we can't rely on hls.py mechanism.
        # Download it ourselves and pass it around in hls_aes128_key.
        keystore_path = urljoin(m3u8_url, self._search_regex(
            r'#EXT-X-KEY:METHOD=AES-128,URI="(?P<ks>.+?)"', m3u8_content,
            "keystore path"))
        key_data = self._request_webpage(keystore_path, video_id,
                                         note="Downloading AES-128 key").read()

        formats = self._extract_m3u8_formats(m3u8_url, video_id, ext='mp4',
                                             entry_protocol='m3u8_native',
                                             m3u8_id='hls', fatal=True)
        if not formats:
            raise ExtractorError("No format found for %s" % video_id)

        description = meta.get('description')
        if description == '-':
            description = None

        return {
            'formats': formats,
            'otp': otp,
            'hls_aes128_key': base64.b64encode(key_data).decode(),
            'id': video_id,
            'duration': int(meta.get('duration', '0')) or None,
            'title': meta.get('title'),
            'description': description,
        }
