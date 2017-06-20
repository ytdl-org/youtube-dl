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

        resolutions = {}
        for fmt in fmt_list:
            mobj = re.search(
                r'^(?P<format_id>\d+)/(?P<width>\d+)[xX](?P<height>\d+)', fmt)
            if mobj:
                resolutions[mobj.group('format_id')] = (
                    int(mobj.group('width')), int(mobj.group('height')))

        formats = []
        for fmt_stream in fmt_stream_map:
            fmt_stream_split = fmt_stream.split('|')
            if len(fmt_stream_split) < 2:
                continue
            format_id, format_url = fmt_stream_split[:2]
            f = {
                'url': lowercase_escape(format_url),
                'format_id': format_id,
                'ext': self._FORMATS_EXT[format_id],
            }
            resolution = resolutions.get(format_id)
            if resolution:
                f.update({
                    'width': resolution[0],
                    'height': resolution[0],
                })
            formats.append(f)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
        }
