# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor


class CloserToTruthIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?closertotruth\.com/series/[^#]+#video-(?P<id>\w+)'
    _TESTS = [{
        'url': 'http://closertotruth.com/series/solutions-the-mind-body-problem#video-3688',
        'md5': '2aa5b8971633d86fe32152827846a5b4',
        'info_dict': {
            'id': '0_zh2b6eqr',
            'ext': 'mov',
            'title': 'ZimDe-010-S',
            'upload_date': '20140307',
            'timestamp': 1394236392,
            'uploader_id': 'CTTXML'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._search_regex(r'<title>(.+) \|.+</title>', webpage, 'video title')

        entry_id = self._search_regex(r'<a[^>]+id="video-%s"[^>]+data-kaltura="([^"]+)' % video_id, webpage, "video entry_id")
        interviewee_name = re.sub(r'(<[^>]+>)', '', self._search_regex(r'<a href="\S+" id="video-' + video_id + '" data-kaltura="\w+">(.+)<span.+<\/a>', webpage, "video interviewee_name"))

        video_title = video_title + ' - ' + interviewee_name

        p_id = self._search_regex(r'<script[^>]+src=["\'].+?partner_id/(\d+)', webpage, "kaltura partner_id")

        return {
            '_type': 'url_transparent',
            'id': entry_id,
            'url': 'kaltura:%s:%s' % (p_id, entry_id),
            'ie_key': 'Kaltura',
            'title': video_title
        }