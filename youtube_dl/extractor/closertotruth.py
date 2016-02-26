# coding: utf-8
from __future__ import unicode_literals

import re
import itertools
import hashlib

from .common import InfoExtractor
from ..utils import (
    int_or_none,
    unified_strdate,
)

class CloserToTruthIE(InfoExtractor):
    _VALID_URL = r'http?://(?:www\.)?closertotruth\.com/series/\S+#video-(?P<id>\w+)'
    _TESTS = [{
        'url': 'http://closertotruth.com/series/solutions-the-mind-body-problem#video-3688',
        'md5': '2aa5b8971633d86fe32152827846a5b4',
        'info_dict': {
            'id': '3688',
            'ext': 'mov',
            'title': 'Solutions to the Mind-Body Problem? -  Dean W.Zimmerman '
        }
    },{
        'url': 'http://closertotruth.com/series/solutions-the-mind-body-problem#video-4048',
        'md5': 'a3882bb6e453720d8a7a3983f58abd04',
        'info_dict': {
            'id': '4048',
            'ext': 'mov',
            'title': 'Solutions to the Mind-Body Problem? -  John Searle '
        }
    }]


    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        
        #compose title for video
        video_title = self._search_regex(r'<title>(.+) \|.+</title>', webpage, 'video title')

        entry_id = self._search_regex(r'<a href="\S+" id="video-'+video_id+'" data-kaltura="(\w+)">.+<span.+<\/a>', webpage, "video entry_id")
        interviewee_name = re.sub(r'(<[^>]+>)', '',self._search_regex(r'<a href="\S+" id="video-'+video_id+'" data-kaltura="\w+">(.+)<span.+<\/a>', webpage, "video interviewee_name"))

        video_title = video_title + ' - ' + interviewee_name

        #extract the partner id for kaltura.com
        p_id = self._search_regex(r'<script src="http://cdnapi\.kaltura\.com/p/(?P<p>\w+)/sp/\w+/\S+/partner_id/\w+"></script>', webpage, "kaltura partner_id")
        
        #request video url at kaltura API
        #from: http://knowledge.kaltura.com/faq/how-retrieve-download-or-streaming-url-using-api-calls
        api_request_url = 'http://www.kaltura.com/p/'+p_id+'/sp/0/playManifest/entryId/'+entry_id+'/protocol/HTTPS/flavorParamId/0/video.mp4'
        api_response = self._download_webpage(api_request_url, video_id)
        
        video_url =  self._search_regex(r'<media url="(\S+)"', api_response, "video url")
        
        return {
            'url': video_url,
            'id': video_id,
            'title': video_title,
        }