# coding: utf-8
from __future__ import unicode_literals

import json
import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
)


class CNETIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?cnet\.com/videos/(?P<id>[^/]+)/'
    _TEST = {
        'url': 'http://www.cnet.com/videos/hands-on-with-microsofts-windows-8-1-update/',
        'md5': '041233212a0d06b179c87cbcca1577b8',
        'info_dict': {
            'id': '56f4ea68-bd21-4852-b08c-4de5b8354c60',
            'ext': 'mp4',
            'title': 'Hands-on with Microsoft Windows 8.1 Update',
            'description': 'The new update to the Windows 8 OS brings improved performance for mouse and keyboard users.',
            'thumbnail': 're:^http://.*/flmswindows8.jpg$',
            'uploader_id': 'sarah.mitroff@cbsinteractive.com',
            'uploader': 'Sarah Mitroff',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)
        data_json = self._html_search_regex(
            r"<div class=\"cnetVideoPlayer\"\s+.*?data-cnet-video-options='([^']+)'",
            webpage, 'data json')
        data = json.loads(data_json)
        vdata = data['video']
        if not vdata:
            vdata = data['videos'][0]
        if not vdata:
            raise ExtractorError('Cannot find video data')

        video_id = vdata['id']
        title = vdata.get('headline')
        if title is None:
            title = vdata.get('title')
        if title is None:
            raise ExtractorError('Cannot find title!')
        description = vdata.get('dek')
        thumbnail = vdata.get('image', {}).get('path')
        author = vdata.get('author')
        if author:
            uploader = '%s %s' % (author['firstName'], author['lastName'])
            uploader_id = author.get('email')
        else:
            uploader = None
            uploader_id = None

        formats = [{
            'format_id': '%s-%s-%s' % (
                f['type'], f['format'],
                int_or_none(f.get('bitrate'), 1000, default='')),
            'url': f['uri'],
            'tbr': int_or_none(f.get('bitrate'), 1000),
        } for f in vdata['files']['data']]
        self._sort_formats(formats)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'formats': formats,
            'description': description,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'thumbnail': thumbnail,
        }
