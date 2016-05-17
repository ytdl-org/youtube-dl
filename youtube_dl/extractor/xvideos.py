from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    clean_html,
    ExtractorError,
    determine_ext,
)


class XVideosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xvideos\.com/video(?P<id>[0-9]+)(?:.*)'
    _TEST = {
        'url': 'http://www.xvideos.com/video4588838/biker_takes_his_girl',
        'md5': '4b46ae6ea5e6e9086e714d883313c0c9',
        'info_dict': {
            'id': '4588838',
            'ext': 'flv',
            'title': 'Biker Takes his Girl',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        video_title = self._html_search_regex(
            r'<title>(.*?)\s+-\s+XVID', webpage, 'title')
        video_thumbnail = self._search_regex(
            r'url_bigthumb=(.+?)&amp', webpage, 'thumbnail', fatal=False)

        formats = []

        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'flv_url=(.+?)&', webpage, 'video URL', default=''))
        if video_url:
            formats.append({'url': video_url})

        player_args = self._search_regex(
            r'(?s)new\s+HTML5Player\((.+?)\)', webpage, ' html5 player', default=None)
        if player_args:
            for arg in player_args.split(','):
                format_url = self._search_regex(
                    r'(["\'])(?P<url>https?://.+?)\1', arg, 'url',
                    default=None, group='url')
                if not format_url:
                    continue
                ext = determine_ext(format_url)
                if ext == 'mp4':
                    formats.append({'url': format_url})
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, video_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': video_title,
            'thumbnail': video_thumbnail,
            'age_limit': 18,
        }
