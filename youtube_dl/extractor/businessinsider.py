# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .jwplatform import JWPlatformIE


class BusinessInsiderIE(InfoExtractor):
    _VALID_URL = r'https?://(?:[^/]+\.)?businessinsider\.(?:com|nl)/(?:[^/]+/)*(?P<id>[^/?#&]+)'
    _TESTS = [{
        'url': 'http://uk.businessinsider.com/how-much-radiation-youre-exposed-to-in-everyday-life-2016-6',
        'md5': 'ca237a53a8eb20b6dc5bd60564d4ab3e',
        'info_dict': {
            'id': 'hZRllCfw',
            'ext': 'mp4',
            'title': "Here's how much radiation you're exposed to in everyday life",
            'description': 'md5:9a0d6e2c279948aadaa5e84d6d9b99bd',
            'upload_date': '20170709',
            'timestamp': 1499606400,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.businessinsider.nl/5-scientifically-proven-things-make-you-less-attractive-2017-7/',
        'only_matching': True,
    }, {
        'url': 'http://www.businessinsider.com/excel-index-match-vlookup-video-how-to-2015-2?IR=T',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        jwplatform_id = self._search_regex(
            (r'data-media-id=["\']([a-zA-Z0-9]{8})',
             r'id=["\']jwplayer_([a-zA-Z0-9]{8})',
             r'id["\']?\s*:\s*["\']?([a-zA-Z0-9]{8})'),
            webpage, 'jwplatform id')
        return self.url_result(
            'jwplatform:%s' % jwplatform_id, ie=JWPlatformIE.ie_key(),
            video_id=video_id)
