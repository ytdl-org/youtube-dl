# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor


class CloserToTruthIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?closertotruth\.com/(series|interviews)/(?:[^#]+#video-)?(?P<id>\d+)'
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
        },
        'url': 'http://closertotruth.com/interviews/1725',
        'md5': 'b00598fd6a38372edb976408f72c5792',
        'info_dict': {
            'id': '0_19qv5rn1',
            'ext': 'mov',
            'title': 'AyaFr-002 - Francisco J. Ayala',
            'upload_date': '20140307',
            'timestamp': 1394236431,
            'uploader_id': 'CTTXML'
        }
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._search_regex(r'<title>(.+) \|.+</title>', webpage, 'video title')

        entry_id = self._search_regex(r'<a[^>]+id="(?:video-%s|embed-kaltura)"[^>]+data-kaltura="([^"]+)' % video_id, webpage, "video entry_id")

        interviewee_name = self._search_regex(r'<div id="(?:node_interview_full_group_white_wrapper|node_interview_series_full_group_ajax_content)"(?:.|\n)*<h3>(.*)<\/h3>', webpage, "video interviewee_name")

        video_title = video_title + ' - ' + interviewee_name

        p_id = self._search_regex(r'<script[^>]+src=["\'].+?partner_id/(\d+)', webpage, "kaltura partner_id")

        return {
            '_type': 'url_transparent',
            'id': entry_id,
            'url': 'kaltura:%s:%s' % (p_id, entry_id),
            'ie_key': 'Kaltura',
            'title': video_title
        }
