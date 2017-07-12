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
        'md5': 'c230c67252874fddd8170e3fd1a45886',
        'info_dict': {
            'id': '1ENcQ_jeCuj7y19s66_Ou9dRP4GKGsodiDQ',
            'ext': 'mp4',
            'title': 'Andreea Banica feat Smiley - Hooky Song (Official Video).mp4',
            'duration': 189,
        },
        'params': {
             'only_matching': True,
        }
    }, {
        'url': 'https://drive.google.com/file/d/0B0Pcx5-LUToEblNxcXRPWmtmS00/view',
        'md5': '3085012a025cf683c67f12010626d897',
        'info_dict': {
            'id': '0B0Pcx5-LUToEblNxcXRPWmtmS00',
            'ext': 'mp4',
            'title': 'bbo20wmv.mp4',
            'duration': 5888,
            'subtitles' : 'mincount:1',
        }
    }, {
        'url': 'https://drive.google.com/file/d/0B7uqFWpTkjfcVi1RaXp1OW1ycFE/edit',
        'md5': 'eab2f1adacf1b283362a9ce28d947db2',
        'info_dict': {
            'id': '0B7uqFWpTkjfcVi1RaXp1OW1ycFE',
            'ext': 'mp4',
            'title': '[18] 101 Dalmatians (1961)',
            'duration': 4756,
            'subtitles' : 'mincount:1',
        },
        'params': {
             'only_matching': True,
        }
    }, {
        'url': 'https://drive.google.com/file/d/0B7klLRUbm38_cXdENHY1cFlHenM/preview',
        'md5': '0eabf6a71f61469b6b4df1c93c57b669',
        'info_dict': {
            'id': '0B7klLRUbm38_cXdENHY1cFlHenM',
            'ext': 'mp4',
            'title': '101 Dalmatians 1961 1080p BluRay x264 AC3 - Ozlem.mp4',
            'duration': 4755,
            'subtitles' : 'mincount:1',
        },
        'params': {
             'only_matching': True,
        }
    }, {
        'url': 'https://drive.google.com/file/d/0B_Cc_rAzzVX9blZZZzZJX2tNYVk/edit',
        'md5': 'a5dd2666a9ee9da523b7a1a6f6c916ae',
        'info_dict': {
            'id': '0B_Cc_rAzzVX9blZZZzZJX2tNYVk',
            'ext': 'mp4',
            'title': 'Buffy 5x04 - Out of My Mind.mkv',
            'duration': 2548,
        },
        'params': {
             'only_matching': True,
        }
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
    _SUBTITLE_FORMATS_EXT = (
         'vtt', 
         'ttml'
    )

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
                    'height': resolution[1],
                })
            formats.append(f)
        self._sort_formats(formats)

        hl = self._search_regex(
            r'"hl"\s*,\s*"([^"]+)', webpage, 'hl')
        ttsurl = self._search_regex(
            r'"ttsurl"\s*,\s*"([^"]+)', webpage, 'ttsurl').encode('utf-8').decode('unicode_escape')
        # the video Id for subtitles will be the last value in the ttsurl query string
        video_subtitles_id = ttsurl.split('=')[-1]

        subtitles = {}
        subtitles_by_country = self._download_xml('https://drive.google.com/timedtext?id=%s&vid=%s&hl=%s&type=list&tlangs=1&v=%s&fmts=1&vssids=1' % (video_id, video_subtitles_id, hl, video_id), video_id)
        subtitle_available_tracks = subtitles_by_country.findall('track')
        for subtitle_track in subtitle_available_tracks:
            subtitle_lang_code = subtitle_track.attrib['lang_code']
            subtitle_format_data = []
            for subtitle_format in self._SUBTITLE_FORMATS_EXT:
                subtitle_format_data.append({
                    'url': 'https://drive.google.com/timedtext?vid=%s&v=%s&type=track&lang=%s&name&kind&fmt=%s' % (video_subtitles_id, video_id, subtitle_lang_code, subtitle_format),
                    'ext': subtitle_format,
                })
            subtitles[subtitle_lang_code] = subtitle_format_data

        return {
            'id': video_id,
            'title': title,
            'thumbnail': self._og_search_thumbnail(webpage, default=None),
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }
