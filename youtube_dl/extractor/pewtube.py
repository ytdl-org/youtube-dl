# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict
from datetime import datetime
import re
import subprocess as sp
import time

from .common import InfoExtractor
from ..utils import CloudFlareSimpleJSChallengeMixin, int_or_none


class PewTubeIE(InfoExtractor, CloudFlareSimpleJSChallengeMixin):
    _VALID_URL = r'https?://(?:www\.)?pew\.tube/user/[^/]+/(?P<id>[^/]+)'
    _TEST = {
        'url': 'https://pew.tube/user/MrBond/4jLJf06',
        'md5': 'TODO: md5 sum of the first 10241 bytes of the video file (use --test)',
        'info_dict': {
            'id': '4jLJf06',
            'ext': 'mp4',
            'title': 'Mr. Bond - Good Old Nationalist',
            'thumbnail': r're:^https?://.*\.jpg$',
            # TODO more properties, either as:
            # * A value
            # * MD5 checksum; start the string with md5:
            # * A regular expression; start the string with re:
            # * Any Python type (for example int or float)
        }
    }

    def set_downloader(self, downloader):
        self._downloader = downloader
        if downloader:
            class Handle503:
                def http_error_503(self, request, response, code, msg, hdrs):
                    return response
            self._downloader._opener.handle_error['http'][503] = [Handle503()]

    def _real_extract(self, url):
        self._do_cloudflare_challenge('pew.tube', url, secure=True)

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<h2 .*upload\-title\-value[^>]+>([^<]+)</h2>', webpage, 'title')
        thumbnail = self._html_search_regex(r'<video .*poster="(https[^"]+)"', webpage, 'thumbnail', fatal=False)
        video_url = self._html_search_regex(r'<(?:audio|video)[^>]+>.*<source.*src="([^"]+)".*</(?:audio|video)>', webpage, 'video URL')
        uploader = self._html_search_regex(r'<h3 .*class="uploader\-name"[^>]+>by \&nbsp;?<a[^>]+>([^<]+)</a>', webpage, 'uploader')
        description = self._html_search_meta('description', webpage, 'description')
        view_count = self._html_search_regex(r'<h3(?:[^>]+)?>(\d+)(?:\s+)[vV]iews</h3>', webpage, 'view count')

        like_count = 0
        for like_class in ('like', 'laugh', 'love',):
            like_count += int(self._html_search_regex(r'<p class="{}">(\d+)</p>'.format(like_class), webpage, '{} count'))

        dislike_count = 0
        for dislike_class in ('dislike', 'sad', 'discount',):
            dislike_count += int(self._html_search_regex(r'<p class="{}">(\d+)</p>'.format(like_class), webpage, '{} count'))

        like_count = None if not like_count else like_count
        dislike_count = None if not dislike_count else dislike_count

        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)
        if not description:
            description = self._og_search_description(webpage)

        # TODO Parse fuzzy upload date
        #upload_date_s = self._html_search_regex(r'<h4>Uploaded ([^<]+)</h4>', webpage, 'upload date')
        #today = datetime.today()
        #upload_date_s = re.sub(r'(?:\s+)ago$', '', upload_date_s)
        #n, unit = re.search('^(?P<n>\d+)\s(?:\s+)?(?P<unit>.*)').groups()
        #unit = unit.lower()
        #if unit == 'month':

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'uploader': uploader,
            'creator': uploader,
            'uploader_url': '/'.join(url.split('/')[:-1]),
            'thumbnail': thumbnail,
            'view_count': int_or_none(view_count),
            'like_count': like_count,
            'dislike_count': dislike_count,
            'url': video_url,
        }
