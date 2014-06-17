# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    compat_urllib_parse,
    compat_urllib_request,
)


class GorillaVidIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gorillavid\.in/(?:embed-)?(?P<id>[0-9a-zA-Z]+)(?:-[0-9]+x[0-9]+\.html)?'

    _TESTS = [{
        'url': 'http://gorillavid.in/06y9juieqpmi',
        'md5': '5ae4a3580620380619678ee4875893ba',
        'info_dict': {
            'id': '06y9juieqpmi',
            'ext': 'flv',
            'title': 'Rebecca Black My Moment Official Music Video Reaction',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://gorillavid.in/embed-z08zf8le23c6-960x480.html',
        'md5': 'c9e293ca74d46cad638e199c3f3fe604',
        'info_dict': {
            'id': 'z08zf8le23c6',
            'ext': 'mp4',
            'title': 'Say something nice',
            'thumbnail': 're:http://.*\.jpg',
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://gorillavid.in/%s' % video_id

        webpage = self._download_webpage(url, video_id)

        fields = dict(re.findall(r'''(?x)<input\s+
            type="hidden"\s+
            name="([^"]+)"\s+
            (?:id="[^"]+"\s+)?
            value="([^"]*)"
            ''', webpage))
        
        if fields['op'] == 'download1':
            post = compat_urllib_parse.urlencode(fields)

            req = compat_urllib_request.Request(url, post)
            req.add_header('Content-type', 'application/x-www-form-urlencoded')

            webpage = self._download_webpage(req, video_id, 'Downloading video page')

        title = self._search_regex(r'style="z-index: [0-9]+;">([0-9a-zA-Z ]+)(?:-.+)?</span>', webpage, 'title')
        thumbnail = self._search_regex(r'image:\'(http[^\']+)\',', webpage, 'thumbnail')
        url = self._search_regex(r'file: \'(http[^\']+)\',', webpage, 'file url')

        formats = [{
            'format_id': 'sd',
            'url': url,
            'ext': determine_ext(url),
            'quality': 1,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
