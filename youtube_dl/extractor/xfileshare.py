# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    sanitized_Request,
    urlencode_postdata,
)


class XFileShareIE(InfoExtractor):
    _SITES = (
        ('daclips.in', 'DaClips'),
        ('filehoot.com', 'FileHoot'),
        ('gorillavid.in', 'GorillaVid'),
        ('movpod.in', 'MovPod'),
        ('powerwatch.pw', 'PowerWatch'),
        ('rapidvideo.ws', 'Rapidvideo.ws'),
        ('thevideobee.to', 'TheVideoBee'),
        ('vidto.me', 'Vidto'),
        ('streamin.to', 'Streamin.To'),
    )

    IE_DESC = 'XFileShare based sites: %s' % ', '.join(list(zip(*_SITES))[1])
    _VALID_URL = (r'https?://(?P<host>(?:www\.)?(?:%s))/(?:embed-)?(?P<id>[0-9a-zA-Z]+)'
                  % '|'.join(re.escape(site) for site in list(zip(*_SITES))[0]))

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
    }, {
        'url': 'http://vidto.me/ku5glz52nqe1.html',
        'info_dict': {
            'id': 'ku5glz52nqe1',
            'ext': 'mp4',
            'title': 'test'
        }
    }, {
        'url': 'http://powerwatch.pw/duecjibvicbu',
        'info_dict': {
            'id': 'duecjibvicbu',
            'ext': 'mp4',
            'title': 'Big Buck Bunny trailer',
        },
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

            post = urlencode_postdata(fields)

            req = sanitized_Request(url, post)
            req.add_header('Content-type', 'application/x-www-form-urlencoded')

            webpage = self._download_webpage(req, video_id, 'Downloading video page')

        title = (self._search_regex(
            [r'style="z-index: [0-9]+;">([^<]+)</span>',
             r'<td nowrap>([^<]+)</td>',
             r'h4-fine[^>]*>([^<]+)<',
             r'>Watch (.+) ',
             r'<h2 class="video-page-head">([^<]+)</h2>'],
            webpage, 'title', default=None) or self._og_search_title(webpage)).strip()
        video_url = self._search_regex(
            [r'file\s*:\s*["\'](http[^"\']+)["\'],',
             r'file_link\s*=\s*\'(https?:\/\/[0-9a-zA-z.\/\-_]+)'],
            webpage, 'file url')
        thumbnail = self._search_regex(
            r'image\s*:\s*["\'](http[^"\']+)["\'],', webpage, 'thumbnail', default=None)

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
