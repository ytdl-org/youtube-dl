# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_request
from .openload import PhantomJSwrapper
from .pornhub import PornHubIE
from ..utils import ExtractorError


class ThumbzillaIE(InfoExtractor):
    """
    ThumbzillaIE is a frontend for other 'Tube' sites (mostly PornHub). ThumbzillaIE will
    parse the video and delegate to the appropriate extractor via a url_result.
    """
    IE_DESC = 'Thumbzilla'
    _VALID_URL = r'https?://(?P<host>(?:www\.)?thumbzilla\.com)/video/(?P<id>[\da-z]+)'

    _TEST = {
        'url': 'https://www.thumbzilla.com/video/ph5c8e8f15b40ff/hot-skinny-girl-gives-you',
        'info_dict': {
            'id': 'ph5c8e8f15b40ff',
            'ext': 'mp4',
            'upload_date': '20190317',
            'age_limit': 18,
            'uploader': 'lizashultz',
            'title': 'Hot skinny girl gives you.',
        }
    }

    def _download_webpage_handle(self, *args, **kwargs):
        def dl(*args, **kwargs):
            return super(ThumbzillaIE, self)._download_webpage_handle(*args, **kwargs)

        webpage, urlh = dl(*args, **kwargs)

        if any(re.search(p, webpage) for p in (
                r'<body\b[^>]+\bonload=["\']go\(\)',
                r'document\.cookie\s*=\s*["\']RNKEY=',
                r'document\.location\.reload\(true\)')):
            url_or_request = args[0]
            url = (url_or_request.get_full_url()
                   if isinstance(url_or_request, compat_urllib_request.Request)
                   else url_or_request)
            phantom = PhantomJSwrapper(self, required_version='2.0')
            phantom.get(url, html=webpage)
            webpage, urlh = dl(*args, **kwargs)

        return webpage, urlh

    def _real_extract(self, url):
        host, video_id = re.match(self._VALID_URL, url).groups()

        if video_id.startswith('ph'):
            return self.url_result('https://pornhub.com/view_video.php?viewkey=%s' % video_id,
                                   video_id=video_id, ie=PornHubIE.ie_key())
        else:
            raise ExtractorError('Unsupported video type')
