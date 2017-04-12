# coding: utf-8

from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    NO_DEFAULT,
    sanitized_Request,
    urlencode_postdata,
)


class NovaMovIE(InfoExtractor):
    IE_NAME = 'novamov'
    IE_DESC = 'NovaMov'

    _VALID_URL_TEMPLATE = r'''(?x)
                            http://
                                (?:
                                    (?:www\.)?%(host)s/(?:file|video|mobile/\#/videos)/|
                                    (?:(?:embed|www)\.)%(host)s/embed(?:\.php|/)?\?(?:.*?&)?\bv=
                                )
                                (?P<id>[a-z\d]{13})
                            '''
    _VALID_URL = _VALID_URL_TEMPLATE % {'host': r'novamov\.com'}

    _HOST = 'www.novamov.com'

    _FILE_DELETED_REGEX = r'This file no longer exists on our servers!</h2>'
    _STEPKEY_REGEX = r'<input type="hidden" name="stepkey" value="(?P<stepkey>"?[^"]+"?)">'
    _URL_REGEX = r'<source src="(?P<url>"?[^"]+"?)" type=\'video/mp4\'>'
    _TITLE_REGEX = r'<meta name="title" content="Watch (?P<title>"?[^"]+"?) online | [a-zA-Z_] " />'
    _URL_TEMPLATE = 'http://%s/video/%s'

    _TEST = None

    def _check_existence(self, webpage, video_id):
        if re.search(self._FILE_DELETED_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id, expected=True)

    def _real_extract(self, url):
        video_id = self._match_id(url)

        url = self._URL_TEMPLATE % (self._HOST, video_id)

        # 1. get the website
        webpage = self._download_webpage(
            url, video_id, 'Downloading video page')

        self._check_existence(webpage, video_id)

        # 2. extract the 'stepkey' value from form
        def extract_stepkey(default=NO_DEFAULT):
            stepkey = self._search_regex(
                self._STEPKEY_REGEX, webpage, 'stepkey', default=default)
            return stepkey

        stepkey = extract_stepkey(default=None)

        if not stepkey:
            raise ExtractorError('stepkey could not be read of %s, please report this error' % video_id, expected=True)

        # 3. send the post request
        data = urlencode_postdata({
            'stepkey': stepkey,
            'submit': 'submit',
        })
        request = sanitized_Request(url, data)
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        webpage = self._download_webpage(request, url)

        # 4. extract the real video url from response
        video_url = self._search_regex(self._URL_REGEX, webpage, 'stepkey')

        if hasattr(self, '_TITLE_REGEX'):
            title = self._search_regex(self._TITLE_REGEX, webpage, 'title')
        else:
            title = str(id)

        if hasattr(self, '_DESCRIPTION_REGEX'):
            description = self._html_search_regex(self._DESCRIPTION_REGEX, webpage, 'description', default='', fatal=False)
        else:
            description = None

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': description
        }


class WholeCloudIE(NovaMovIE):
    IE_NAME = 'wholecloud'
    IE_DESC = 'WholeCloud'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': r'(?:wholecloud\.net|movshare\.(?:net|sx|ag))'}

    _HOST = 'www.wholecloud.net'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<meta name="title" content="Watch (?P<title>"?[^"]+"?) online | [a-zA-Z_] " />'
    _DESCRIPTION_REGEX = r'<strong>Description:</strong> ([^<]+)</p>'

    _TESTS = [{
        'url': 'http://www.wholecloud.net/video/e1de95371c94a',
        'info_dict': {
            'id': 'e1de95371c94a',
            'ext': 'mp4',
            'title': 'Big Buck Bunny UHD 4K 60fps',
            'description': 'No description',
        },
        'md5': '909304eb0b75ef231ceb72d84fade33d',
    }, {
        'url': 'http://www.wholecloud.net/video/e1de95371c94a',
        'only_matching': True,
    }]


class NowVideoIE(NovaMovIE):
    IE_NAME = 'nowvideo'
    IE_DESC = 'NowVideo'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': r'nowvideo\.(?:to|ch|ec|sx|eu|at|ag|co|li)'}

    _HOST = 'www.nowvideo.to'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<h4>([^<]+)</h4>'
    _DESCRIPTION_REGEX = r'</h4>\s*<p>([^<]+)</p>'

    _TESTS = [{
        'url': 'http://www.nowvideo.sx/video/461ebb17e1a83',
        'info_dict': {
            'id': '461ebb17e1a83',
            'ext': 'mp4',
            'title': 'Big Buck Bunny UHD 4K 60fps',
            'description': 'No description',
        },
        'md5': '909304eb0b75ef231ceb72d84fade33d',
    }, {
        'url': 'http://www.nowvideo.sx/video/461ebb17e1a83',
        'only_matching': True,
    }]


# VideoWeed is now BitVid
class BitVidIE(NovaMovIE):
    IE_NAME = 'bitvid'
    IE_DESC = 'Bitvid'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': r'bitvid\.(?:sx)'}

    _HOST = 'www.bitvid.sx'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'
    _TITLE_REGEX = r'<h1 class="text_shadow">([^<]+)</h1>'
    _URL_TEMPLATE = 'http://%s/file/%s'

    _TESTS = [{
        'url': 'http://www.bitvid.sx/file/bceedaa7b969c',
        'info_dict': {
            'id': 'bceedaa7b969c',
            'ext': 'mp4',
            'title': 'Big Buck Bunny UHD 4K 60fps'
        },
        'md5': '909304eb0b75ef231ceb72d84fade33d',
    }, {
        'url': 'http://www.bitvid.sx/file/bceedaa7b969c',
        'only_matching': True,
    }]


class CloudTimeIE(NovaMovIE):
    IE_NAME = 'cloudtime'
    IE_DESC = 'CloudTime'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': r'cloudtime\.to'}

    _HOST = 'www.cloudtime.to'

    _FILE_DELETED_REGEX = r'>This file no longer exists on our servers.<'

    _TEST = None


class AuroraVidIE(NovaMovIE):
    IE_NAME = 'auroravid'
    IE_DESC = 'AuroraVid'

    _VALID_URL = NovaMovIE._VALID_URL_TEMPLATE % {'host': r'auroravid\.to'}

    _HOST = 'www.auroravid.to'

    _FILE_DELETED_REGEX = r'This file no longer exists on our servers!<'

    _TESTS = [{
        'url': 'http://www.auroravid.to/video/27851f1e57c95',
        'info_dict': {
            'id': '27851f1e57c95',
            'ext': 'mp4',
            'title': 'Big Buck Bunny UHD 4K 60fps',
        },
        'md5': '909304eb0b75ef231ceb72d84fade33d',
    }, {
        'url': 'http://www.auroravid.to/video/27851f1e57c95',
        'only_matching': True,
    }]
