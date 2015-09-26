# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    ExtractorError,
    encode_dict,
    int_or_none,
)


class GorillaVidIE(InfoExtractor):
    IE_DESC = 'GorillaVid.in, daclips.in, movpod.in, fastvideo.in, realvid.net and filehoot.com'
    _VALID_URL = r'''(?x)
        https?://(?P<host>(?:www\.)?
            (?:daclips\.in|gorillavid\.in|movpod\.in|fastvideo\.in|realvid\.net|filehoot\.com))/
        (?:embed-)?(?P<id>[0-9a-zA-Z]+)(?:-[0-9]+x[0-9]+\.html)?
    '''

    _FILE_NOT_FOUND_REGEX = r'>(?:404 - )?File Not Found<'

    _TESTS = [{
        'url': 'http://gorillavid.in/06y9juieqpmi',
        'md5': '5ae4a3580620380619678ee4875893ba',
        'info_dict': {
            'id': '06y9juieqpmi',
            'ext': 'flv',
            'title': 'Rebecca Black My Moment Official Music Video Reaction-6GK87Rc8bzQ',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://gorillavid.in/embed-z08zf8le23c6-960x480.html',
        'only_matching': True,
    }, {
        'url': 'http://daclips.in/3rso4kdn6f9m',
        'md5': '1ad8fd39bb976eeb66004d3a4895f106',
        'info_dict': {
            'id': '3rso4kdn6f9m',
            'ext': 'mp4',
            'title': 'Micro Pig piglets ready on 16th July 2009-bG0PdrCdxUc',
            'thumbnail': 're:http://.*\.jpg',
        }
    }, {
        # video with countdown timeout
        'url': 'http://fastvideo.in/1qmdn1lmsmbw',
        'md5': '8b87ec3f6564a3108a0e8e66594842ba',
        'info_dict': {
            'id': '1qmdn1lmsmbw',
            'ext': 'mp4',
            'title': 'Man of Steel - Trailer',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://realvid.net/ctn2y6p2eviw',
        'md5': 'b2166d2cf192efd6b6d764c18fd3710e',
        'info_dict': {
            'id': 'ctn2y6p2eviw',
            'ext': 'flv',
            'title': 'rdx 1955',
            'thumbnail': 're:http://.*\.jpg',
        },
    }, {
        'url': 'http://movpod.in/0wguyyxi1yca',
        'only_matching': True,
    }, {
        'url': 'http://filehoot.com/3ivfabn7573c.html',
        'info_dict': {
            'id': '3ivfabn7573c',
            'ext': 'mp4',
            'title': 'youtube-dl test video \'äBaW_jenozKc.mp4.mp4',
            'thumbnail': 're:http://.*\.jpg',
        }
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://%s/%s' % (mobj.group('host'), video_id)
        webpage = self._download_webpage(url, video_id)

        if re.search(self._FILE_NOT_FOUND_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

        fields = self._hidden_inputs(webpage)

        if fields['op'] == 'download1':
            countdown = int_or_none(self._search_regex(
                r'<span id="countdown_str">(?:[Ww]ait)?\s*<span id="cxc">(\d+)</span>\s*(?:seconds?)?</span>',
                webpage, 'countdown', default=None))
            if countdown:
                self._sleep(countdown, video_id)

            post = compat_urllib_parse.urlencode(encode_dict(fields))

            req = compat_urllib_request.Request(url, post)
            req.add_header('Content-type', 'application/x-www-form-urlencoded')

            webpage = self._download_webpage(req, video_id, 'Downloading video page')

        title = self._search_regex(
            [r'style="z-index: [0-9]+;">([^<]+)</span>', r'<td nowrap>([^<]+)</td>', r'>Watch (.+) '],
            webpage, 'title', default=None) or self._og_search_title(webpage)
        video_url = self._search_regex(
            r'file\s*:\s*["\'](http[^"\']+)["\'],', webpage, 'file url')
        thumbnail = self._search_regex(
            r'image\s*:\s*["\'](http[^"\']+)["\'],', webpage, 'thumbnail', fatal=False)

        formats = [{
            'format_id': 'sd',
            'url': video_url,
            'quality': 1,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
