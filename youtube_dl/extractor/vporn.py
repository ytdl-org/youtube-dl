from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    parse_duration,
    parse_resolution,
    str_to_int,
)


class VpornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?vporn\.com/[^/]+/(?P<display_id>[^/]+)/(?P<id>\d+)'
    _TESTS = [
        {
            'url': 'http://www.vporn.com/masturbation/violet-on-her-th-birthday/497944/',
            'md5': 'facf37c1b86546fa0208058546842c55',
            'info_dict': {
                'id': '497944',
                'display_id': 'violet-on-her-th-birthday',
                'ext': 'mp4',
                'title': 'Violet on her 19th birthday',
                'description': 'Violet dances in front of the camera which is sure to get you horny.',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'kileyGrope',
                'categories': ['Masturbation', 'Teen'],
                'duration': 393,
                'age_limit': 18,
                'view_count': int,
            },
            'skip': 'video removed',
        },
        {
            'url': 'http://www.vporn.com/female/hana-shower/523564/',
            'md5': 'ced35a4656198a1664cf2cda1575a25f',
            'info_dict': {
                'id': '523564',
                'display_id': 'hana-shower',
                'ext': 'mp4',
                'title': 'Hana Shower',
                'description': 'Hana showers at the bathroom.',
                'thumbnail': r're:^https?://.*\.jpg$',
                'uploader': 'Hmmmmm',
                'categories': ['Big Boobs', 'Erotic', 'Teen', 'Female', '720p'],
                'duration': 588,
                'age_limit': 18,
                'view_count': int,
            }
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        errmsg = 'This video has been deleted due to Copyright Infringement or by the account owner!'
        if errmsg in webpage:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, errmsg), expected=True)

        title = self._html_search_regex(
            r'videoname\s*=\s*\'([^\']+)\'', webpage, 'title').strip()

        description = self._search_regex(r'[^>]*class="(?:sidebar-box)"[^>]*>[\n]<p>(.*?)</p>',
                                         webpage, 'description', fatal=False)

        thumbnail = self._search_regex(r'<video[^>]+poster="([^"])"', webpage, 'thumbnail', default=None) or self._search_regex(r'posterurl\s=\s\'([^\']+)', webpage, 'thumbnail', fatal=False)

        uploader = self._search_regex(r'class="avatarname">(.*?)</span>',
                                      webpage, 'uploader', fatal=False)

        categories = re.findall(r'<a[^>]*class="tags links"[^>]*>([^<]+)</a>', webpage)

        duration = parse_duration(self._search_regex(
            r'class="durat-img"[^>]*>\s*(\d+ min \d+ sec)',
            webpage, 'duration', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'class="view-count">[\n]([\d,\.]+) [Vv]iews[\n]<',
            webpage, 'view count', fatal=False))

        comment_count = str_to_int(self._html_search_regex(
            r"'Comments \(([\d,\.]+)\)'",
            webpage, 'comment count', default=None))

        formats = []
        for mobj in re.finditer(r'<source[^>]+src="([^"]+)"[^>]+label="([^"]+)[^>]*>', webpage):
            f = parse_resolution(mobj.group(2))
            f.update({
                'url': mobj.group(1),
                'format_id': mobj.group(2),
            })
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'categories': categories,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'age_limit': 18,
            'formats': formats,
        }
