# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_parse,
    compat_urllib_request,
)


class FiredriveIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?firedrive\.com/' + \
                 '(?:file|embed)/(?P<id>[0-9a-zA-Z]+)'
    _FILE_DELETED_REGEX = r'<div class="removed_file_image">'

    _TESTS = [{
        'url': 'https://www.firedrive.com/file/FEB892FA160EBD01',
        'md5': 'd5d4252f80ebeab4dc2d5ceaed1b7970',
        'info_dict': {
            'id': 'FEB892FA160EBD01',
            'ext': 'flv',
            'title': 'bbb_theora_486kbit.flv',
            'thumbnail': 're:^http://.*\.jpg$',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://firedrive.com/file/%s' % video_id

        webpage = self._download_webpage(url, video_id)

        if re.search(self._FILE_DELETED_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        fields = dict(re.findall(r'''(?x)<input\s+
            type="hidden"\s+
            name="([^"]+)"\s+
            value="([^"]*)"
            ''', webpage))

        post = compat_urllib_parse.urlencode(fields)
        req = compat_urllib_request.Request(url, post)
        req.add_header('Content-type', 'application/x-www-form-urlencoded')

        # Apparently, this header is required for confirmation to work.
        req.add_header('Host', 'www.firedrive.com')

        webpage = self._download_webpage(req, video_id,
                                         'Downloading video page')

        title = self._search_regex(r'class="external_title_left">(.+)</div>',
                                   webpage, 'title')
        thumbnail = self._search_regex(r'image:\s?"(//[^\"]+)', webpage,
                                       'thumbnail', fatal=False)
        if thumbnail is not None:
            thumbnail = 'http:' + thumbnail

        ext = self._search_regex(r'type:\s?\'([^\']+)\',',
                                 webpage, 'extension', fatal=False)
        video_url = self._search_regex(
            r'file:\s?loadURL\(\'(http[^\']+)\'\),', webpage, 'file url')

        formats = [{
            'format_id': 'sd',
            'url': video_url,
            'ext': ext,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
