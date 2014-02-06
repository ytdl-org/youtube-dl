# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import ExtractorError


class NDRIE(InfoExtractor):
    IE_NAME = 'ndr'
    IE_DESC = 'NDR.de - Mediathek'
    _VALID_URL = r'https?://www\.ndr\.de/.+?(?P<id>\d+)\.html'

    _TESTS = [
        # video
        {
            'url': 'http://www.ndr.de/fernsehen/sendungen/hallo_niedersachsen/media/hallonds19925.html',
            'md5': '20eba151ff165f386643dad9c1da08f7',
            'info_dict': {
                'id': '19925',
                'ext': 'mp4',
                'title': 'Hallo Niedersachsen  ',
                'description': 'Bei Hallo Niedersachsen um 19:30 Uhr erfahren Sie alles, was am Tag in Niedersachsen los war.',
                'duration': 1722,
            },
        },
        # audio
        {
            'url': 'http://www.ndr.de/903/audio191719.html',
            'md5': '41ed601768534dd18a9ae34d84798129',
            'info_dict': {
                'id': '191719',
                'ext': 'mp3',
                'title': '"Es war schockierend"',
                'description': 'md5:ed7ff8364793545021a6355b97e95f10',
                'duration': 112,
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        title = self._og_search_title(page)
        description = self._og_search_description(page)

        mobj = re.search(
            r'<div class="duration"><span class="min">(?P<minutes>\d+)</span>:<span class="sec">(?P<seconds>\d+)</span></div>',
            page)
        duration = int(mobj.group('minutes')) * 60 + int(mobj.group('seconds')) if mobj else None

        formats = []

        mp3_url = re.search(r'''{src:'(?P<audio>[^']+)', type:"audio/mp3"},''', page)
        if mp3_url:
            formats.append({
                'url': mp3_url.group('audio'),
                'format_id': 'mp3',
            })

        thumbnail = None

        video_url = re.search(r'''3: {src:'(?P<video>.+?)\.hi\.mp4', type:"video/mp4"},''', page)
        if video_url:
            thumbnail = self._html_search_regex(r'(?m)title: "NDR PLAYER",\s*poster: "([^"]+)",',
                page, 'thumbnail', fatal=False)
            if thumbnail:
                thumbnail = 'http://www.ndr.de' + thumbnail
            for format_id in ['lo', 'hi', 'hq']:
                formats.append({
                    'url': '%s.%s.mp4' % (video_url.group('video'), format_id),
                    'format_id': format_id,
                })

        if not formats:
            raise ExtractorError('No media links available for %s' % video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }