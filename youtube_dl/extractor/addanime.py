from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_HTTPError,
    compat_str,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_urlparse,
)
from ..utils import (
    ExtractorError,
    qualities,
)


class AddAnimeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?add-anime\.net/(?:watch_video\.php\?(?:.*?)v=|video/)(?P<id>[\w_]+)'
    _TESTS = [{
        'url': 'http://www.add-anime.net/watch_video.php?v=24MR3YO5SAS9',
        'md5': '72954ea10bc979ab5e2eb288b21425a0',
        'info_dict': {
            'id': '24MR3YO5SAS9',
            'ext': 'mp4',
            'description': 'One Piece 606',
            'title': 'One Piece 606',
        },
        'skip': 'Video is gone',
    }, {
        'url': 'http://add-anime.net/video/MDUGWYKNGBD8/One-Piece-687',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        try:
            webpage = self._download_webpage(url, video_id)
        except ExtractorError as ee:
            if not isinstance(ee.cause, compat_HTTPError) or \
               ee.cause.code != 503:
                raise

            redir_webpage = ee.cause.read().decode('utf-8')
            action = self._search_regex(
                r'<form id="challenge-form" action="([^"]+)"',
                redir_webpage, 'Redirect form')
            vc = self._search_regex(
                r'<input type="hidden" name="jschl_vc" value="([^"]+)"/>',
                redir_webpage, 'redirect vc value')
            av = re.search(
                r'a\.value = ([0-9]+)[+]([0-9]+)[*]([0-9]+);',
                redir_webpage)
            if av is None:
                raise ExtractorError('Cannot find redirect math task')
            av_res = int(av.group(1)) + int(av.group(2)) * int(av.group(3))

            parsed_url = compat_urllib_parse_urlparse(url)
            av_val = av_res + len(parsed_url.netloc)
            confirm_url = (
                parsed_url.scheme + '://' + parsed_url.netloc +
                action + '?' +
                compat_urllib_parse_urlencode({
                    'jschl_vc': vc, 'jschl_answer': compat_str(av_val)}))
            self._download_webpage(
                confirm_url, video_id,
                note='Confirming after redirect')
            webpage = self._download_webpage(url, video_id)

        FORMATS = ('normal', 'hq')
        quality = qualities(FORMATS)
        formats = []
        for format_id in FORMATS:
            rex = r"var %s_video_file = '(.*?)';" % re.escape(format_id)
            video_url = self._search_regex(rex, webpage, 'video file URLx',
                                           fatal=False)
            if not video_url:
                continue
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'quality': quality(format_id),
            })
        self._sort_formats(formats)
        video_title = self._og_search_title(webpage)
        video_description = self._og_search_description(webpage)

        return {
            '_type': 'video',
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'description': video_description
        }
