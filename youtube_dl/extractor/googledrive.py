from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    lowercase_escape,
)


class GoogleDriveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)|video\.google\.com/get_player\?.*?docid=)(?P<id>[a-zA-Z0-9_-]{28,})'
    _TESTS = [{
        'url': 'https://drive.google.com/file/d/0ByeS4oOUV-49Zzh4R1J6R09zazQ/edit?pli=1',
        'md5': 'd109872761f7e7ecf353fa108c0dbe1e',
        'info_dict': {
            'id': '0ByeS4oOUV-49Zzh4R1J6R09zazQ',
            'ext': 'mp4',
            'title': 'Big Buck Bunny.mp4',
            'duration': 45,
        }
    }, {
        # video id is longer than 28 characters
        'url': 'https://drive.google.com/file/d/1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ/edit',
        'only_matching': True,
    }]
    _FORMATS_EXT = {
        '5': 'flv',
        '6': 'flv',
        '13': '3gp',
        '17': '3gp',
        '18': 'mp4',
        '22': 'mp4',
        '34': 'flv',
        '35': 'flv',
        '36': '3gp',
        '37': 'mp4',
        '38': 'mp4',
        '43': 'webm',
        '44': 'webm',
        '45': 'webm',
        '46': 'webm',
        '59': 'mp4',
    }

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src="https?://(?:video\.google\.com/get_player\?.*?docid=|(?:docs|drive)\.google\.com/file/d/)(?P<id>[a-zA-Z0-9_-]{28,})',
            webpage)
        if mobj:
            return 'https://drive.google.com/file/d/%s' % mobj.group('id')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://docs.google.com/file/d/%s' % video_id, video_id)

        reason = self._search_regex(r'"reason"\s*,\s*"([^"]+)', webpage, 'reason', default=None)
        if reason:
            raise ExtractorError(reason)

        title = self._search_regex(r'"title"\s*,\s*"([^"]+)', webpage, 'title')
        duration = int_or_none(self._search_regex(
            r'"length_seconds"\s*,\s*"([^"]+)', webpage, 'length seconds', default=None))
        fmt_stream_map = self._search_regex(
            r'"fmt_stream_map"\s*,\s*"([^"]+)', webpage, 'fmt stream map').split(',')
        fmt_list = self._search_regex(r'"fmt_list"\s*,\s*"([^"]+)', webpage, 'fmt_list').split(',')

        formats = []
        for fmt, fmt_stream in zip(fmt_list, fmt_stream_map):
            fmt_id, fmt_url = fmt_stream.split('|')
            resolution = fmt.split('/')[1]
            width, height = resolution.split('x')
            formats.append({
                'url': lowercase_escape(fmt_url),
                'format_id': fmt_id,
                'resolution': resolution,
                'width': int_or_none(width),
                'height': int_or_none(height),
                'ext': self._FORMATS_EXT[fmt_id],
            })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
        }
