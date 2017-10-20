# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from .nexx import NexxIE
from ..utils import extract_attributes


class FunkIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funk\.net/(?:mix|channel)/(?:[^/]+/)*(?P<id>[^?/#]+)'
    _TESTS = [{
        'url': 'https://www.funk.net/mix/59d65d935f8b160001828b5b/0/59d517e741dca10001252574/',
        'md5': '4d40974481fa3475f8bccfd20c5361f8',
        'info_dict': {
            'id': '716599',
            'ext': 'mp4',
            'title': 'Neue Rechte Welle',
            'description': 'md5:a30a53f740ffb6bfd535314c2cc5fb69',
            'timestamp': 1501337639,
            'upload_date': '20170729',
        },
        'params': {
            'format': 'bestvideo',
            'skip_download': True,
        },
    }, {
        'url': 'https://www.funk.net/channel/59d5149841dca100012511e3/0/59d52049999264000182e79d/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        domain_id = NexxIE._extract_domain_id(webpage) or '741'
        nexx_id = extract_attributes(self._search_regex(
            r'(<div[^>]id=["\']mediaplayer-funk[^>]+>)',
            webpage, 'media player'))['data-id']

        return self.url_result(
            'nexx:%s:%s' % (domain_id, nexx_id), ie=NexxIE.ie_key(),
            video_id=nexx_id)
