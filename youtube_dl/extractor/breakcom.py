from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    int_or_none,
    parse_age_limit,
)


class BreakIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<site>break|screenjunkies)\.com/video/(?P<display_id>[^/]+?)(?:-(?P<id>\d+))?(?:[/?#&]|$)'
    _TESTS = [{
        'url': 'http://www.break.com/video/when-girls-act-like-guys-2468056',
        'info_dict': {
            'id': '2468056',
            'ext': 'mp4',
            'title': 'When Girls Act Like D-Bags',
            'age_limit': 13,
        }
    }, {
        'url': 'http://www.screenjunkies.com/video/best-quentin-tarantino-movie-2841915',
        'md5': '5c2b686bec3d43de42bde9ec047536b0',
        'info_dict': {
            'id': '2841915',
            'display_id': 'best-quentin-tarantino-movie',
            'ext': 'mp4',
            'title': 'Best Quentin Tarantino Movie',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 3671,
            'age_limit': 13,
            'tags': list,
        },
    }, {
        'url': 'http://www.screenjunkies.com/video/honest-trailers-the-dark-knight',
        'info_dict': {
            'id': '2348808',
            'display_id': 'honest-trailers-the-dark-knight',
            'ext': 'mp4',
            'title': 'Honest Trailers - The Dark Knight',
            'thumbnail': r're:^https?://.*\.(?:jpg|png)',
            'age_limit': 10,
            'tags': list,
        },
    }, {
        # requires subscription but worked around
        'url': 'http://www.screenjunkies.com/video/knocking-dead-ep-1-the-show-so-far-3003285',
        'info_dict': {
            'id': '3003285',
            'display_id': 'knocking-dead-ep-1-the-show-so-far',
            'ext': 'mp4',
            'title': 'State of The Dead Recap: Knocking Dead Pilot',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 3307,
            'age_limit': 13,
            'tags': list,
        },
    }, {
        'url': 'http://www.break.com/video/ugc/baby-flex-2773063',
        'only_matching': True,
    }]

    _DEFAULT_BITRATES = (48, 150, 320, 496, 864, 2240, 3264)

    def _real_extract(self, url):
        site, display_id, video_id = re.match(self._VALID_URL, url).groups()

        if not video_id:
            webpage = self._download_webpage(url, display_id)
            video_id = self._search_regex(
                (r'src=["\']/embed/(\d+)', r'data-video-content-id=["\'](\d+)'),
                webpage, 'video id')

        webpage = self._download_webpage(
            'http://www.%s.com/embed/%s' % (site, video_id),
            display_id, 'Downloading video embed page')
        embed_vars = self._parse_json(
            self._search_regex(
                r'(?s)embedVars\s*=\s*({.+?})\s*</script>', webpage, 'embed vars'),
            display_id)

        youtube_id = embed_vars.get('youtubeId')
        if youtube_id:
            return self.url_result(youtube_id, 'Youtube')

        title = embed_vars['contentName']

        formats = []
        bitrates = []
        for f in embed_vars.get('media', []):
            if not f.get('uri') or f.get('mediaPurpose') != 'play':
                continue
            bitrate = int_or_none(f.get('bitRate'))
            if bitrate:
                bitrates.append(bitrate)
            formats.append({
                'url': f['uri'],
                'format_id': 'http-%d' % bitrate if bitrate else 'http',
                'width': int_or_none(f.get('width')),
                'height': int_or_none(f.get('height')),
                'tbr': bitrate,
                'format': 'mp4',
            })

        if not bitrates:
            # When subscriptionLevel > 0, i.e. plus subscription is required
            # media list will be empty. However, hds and hls uris are still
            # available. We can grab them assuming bitrates to be default.
            bitrates = self._DEFAULT_BITRATES

        auth_token = embed_vars.get('AuthToken')

        def construct_manifest_url(base_url, ext):
            pieces = [base_url]
            pieces.extend([compat_str(b) for b in bitrates])
            pieces.append('_kbps.mp4.%s?%s' % (ext, auth_token))
            return ','.join(pieces)

        if bitrates and auth_token:
            hds_url = embed_vars.get('hdsUri')
            if hds_url:
                formats.extend(self._extract_f4m_formats(
                    construct_manifest_url(hds_url, 'f4m'),
                    display_id, f4m_id='hds', fatal=False))
            hls_url = embed_vars.get('hlsUri')
            if hls_url:
                formats.extend(self._extract_m3u8_formats(
                    construct_manifest_url(hls_url, 'm3u8'),
                    display_id, 'mp4', entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'thumbnail': embed_vars.get('thumbUri'),
            'duration': int_or_none(embed_vars.get('videoLengthInSeconds')) or None,
            'age_limit': parse_age_limit(embed_vars.get('audienceRating')),
            'tags': embed_vars.get('tags', '').split(','),
            'formats': formats,
        }
