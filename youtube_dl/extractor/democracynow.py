# coding: utf-8
from __future__ import unicode_literals

import json
import time
import hmac
import hashlib
import itertools
import re
from ..utils import (
    ExtractorError,
    int_or_none,
    parse_age_limit,
    parse_iso8601,
)
from ..compat import compat_urllib_request
from .common import InfoExtractor


class DemocracynowIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?democracynow.org/?(?P<id>[^\?]*)'
    IE_NAME = 'democracynow'
    _TESTS = [{
        'url': 'http://www.democracynow.org/shows/2015/7/3',
        'info_dict': {
            'id': '2015-0703-001',
            'ext': 'mp4',
            'title': 'July 03, 2015 - Democracy Now!',
            'description': 'A daily independent global news hour with Amy Goodman & Juan Gonz\xe1lez "What to the Slave is 4th of July?": James Earl Jones Reads Frederick Douglass\u2019 Historic Speech : "This Flag Comes Down Today": Bree Newsome Scales SC Capitol Flagpole, Takes Down Confederate Flag : "We Shall Overcome": Remembering Folk Icon, Activist Pete Seeger in His Own Words & Songs',
            'uploader': 'Democracy Now',
            'upload_date': None,
        },
     },{
        'url': 'http://www.democracynow.org/2015/7/3/this_flag_comes_down_today_bree',
        'info_dict': {
            'id': '2015-0703-001',
            'ext': 'mp4',
            'title': '"This Flag Comes Down Today": Bree Newsome Scales SC Capitol Flagpole, Takes Down Confederate Flag',
            'description': 'md5:4d2bc4f0d29f5553c2210a4bc7761a21',
            'uploader': 'Democracy Now',
            'upload_date': None,
        },

    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)
        base_host = re.search(r'^(.+?://[^/]+)', url).group(1)
        if display_id == '':
            display_id = 'home'
        webpage = self._download_webpage(url, display_id)
        re_desc = re.search(r'<meta property=.og:description. content=(["\'])(.+?)\1',webpage,re.DOTALL)
        description = re_desc.group(2) if re_desc else ''

        jstr = self._search_regex(r'({.+?"related_video_xml".+?})', webpage, 'json', default=None)
        js = self._parse_json(jstr, display_id)
        video_id = None
        formats = []
        subtitles = {}
        for key in ('caption_file','.......'):
            # ....... = pending vtt support that doesn't clobber srt 'chapter_file':
            url = js.get(key,'')
            if url == '' or url == None:
                continue
            if not re.match(r'^https?://',url):
                url = base_host + url
            ext = re.search(r'\.([^\.]+)$',url).group(1)
            subtitles['eng'] = [{
                'ext': ext,
                'url': url,
            }]
        for key in ('file', 'audio'):
            url = js.get(key,'')
            if url == '' or url == None:
                continue
            if not re.match(r'^https?://',url):
                url = base_host + url
            purl = re.search(r'/(?P<dir>[^/]+)/(?:dn)?(?P<fn>[^/]+?)\.(?P<ext>[^\.\?]+)(?P<hasparams>\?|$)',url)
            if video_id == None:
                video_id = purl.group('fn')
            if js.get('start') != None:
                url += '&' if purl.group('hasparams') == '?' else '?'
                url = url + 'start='+str(js.get('start'))
            formats.append({
                'format_id': purl.group('dir'),
                'ext': purl.group('ext'),
                'url': url,
            })
        self._sort_formats(formats)
        ret = {
            'id': video_id,
            'title': js.get('title'),
            'description': description,
            'uploader': 'Democracy Now',
#            'thumbnails': thumbnails,
            'subtitles': subtitles,
            'formats': formats,
        }
        return ret
#