# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..compat import (
    compat_parse_qs,
    compat_str,
)
from ..utils import (
    int_or_none,
    try_get,
    unified_timestamp,
)


class PornFlipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornflip\.com/(?:v|embed)/(?P<id>[0-9A-Za-z]{11})'
    _TESTS = [{
        'url': 'https://www.pornflip.com/v/wz7DfNhMmep',
        'md5': '98c46639849145ae1fd77af532a9278c',
        'info_dict': {
            'id': 'wz7DfNhMmep',
            'ext': 'mp4',
            'title': '2 Amateurs swallow make his dream cumshots true',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 112,
            'timestamp': 1481655502,
            'upload_date': '20161213',
            'uploader_id': '106786',
            'uploader': 'figifoto',
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'https://www.pornflip.com/embed/wz7DfNhMmep',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.pornflip.com/v/%s' % video_id, video_id)

        flashvars = compat_parse_qs(self._search_regex(
            r'<embed[^>]+flashvars=(["\'])(?P<flashvars>(?:(?!\1).)+)\1',
            webpage, 'flashvars', group='flashvars'))

        title = flashvars['video_vars[title]'][0]

        def flashvar(kind):
            return try_get(
                flashvars, lambda x: x['video_vars[%s]' % kind][0], compat_str)

        formats = []
        for key, value in flashvars.items():
            if not (value and isinstance(value, list)):
                continue
            format_url = value[0]
            if key == 'video_vars[hds_manifest]':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
                continue
            height = self._search_regex(
                r'video_vars\[video_urls\]\[(\d+)', key, 'height', default=None)
            if not height:
                continue
            formats.append({
                'url': format_url,
                'format_id': 'http-%s' % height,
                'height': int_or_none(height),
            })
        self._sort_formats(formats)

        uploader = self._html_search_regex(
            (r'<span[^>]+class="name"[^>]*>\s*<a[^>]+>\s*<strong>(?P<uploader>[^<]+)',
             r'<meta[^>]+content=(["\'])[^>]*\buploaded by (?P<uploader>.+?)\1'),
            webpage, 'uploader', fatal=False, group='uploader')

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'thumbnail': flashvar('big_thumb'),
            'duration': int_or_none(flashvar('duration')),
            'timestamp': unified_timestamp(self._html_search_meta(
                'uploadDate', webpage, 'timestamp')),
            'uploader_id': flashvar('author_id'),
            'uploader': uploader,
            'view_count': int_or_none(flashvar('views')),
            'age_limit': 18,
        }
