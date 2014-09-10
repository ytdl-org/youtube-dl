# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    int_or_none,
    urlencode_postdata,
)


class HostingBulkIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:www\.)?hostingbulk\.com/
        (?:embed-)?(?P<id>[A-Za-z0-9]{12})(?:-\d+x\d+)?\.html'''
    _FILE_DELETED_REGEX = r'<b>File Not Found</b>'
    _TEST = {
        'url': 'http://hostingbulk.com/n0ulw1hv20fm.html',
        'md5': '6c8653c8ecf7ebfa83b76e24b7b2fe3f',
        'info_dict': {
            'id': 'n0ulw1hv20fm',
            'ext': 'mp4',
            'title': 'md5:5afeba33f48ec87219c269e054afd622',
            'filesize': 6816081,
            'thumbnail': 're:^http://.*\.jpg$',
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'http://hostingbulk.com/{0:}.html'.format(video_id)

        # Custom request with cookie to set language to English, so our file
        # deleted regex would work.
        request = compat_urllib_request.Request(
            url, headers={'Cookie': 'lang=english'})
        webpage = self._download_webpage(request, video_id)

        if re.search(self._FILE_DELETED_REGEX, webpage) is not None:
            raise ExtractorError('Video %s does not exist' % video_id,
                                 expected=True)

        title = self._html_search_regex(r'<h3>(.*?)</h3>', webpage, 'title')
        filesize = int_or_none(
            self._search_regex(
                r'<small>\((\d+)\sbytes?\)</small>',
                webpage,
                'filesize',
                fatal=False
            )
        )
        thumbnail = self._search_regex(
            r'<img src="([^"]+)".+?class="pic"',
            webpage, 'thumbnail', fatal=False)

        fields = dict(re.findall(r'''(?x)<input\s+
            type="hidden"\s+
            name="([^"]+)"\s+
            value="([^"]*)"
            ''', webpage))

        request = compat_urllib_request.Request(url, urlencode_postdata(fields))
        request.add_header('Content-type', 'application/x-www-form-urlencoded')
        response = self._request_webpage(request, video_id,
                                         'Submiting download request')
        video_url = response.geturl()

        formats = [{
            'format_id': 'sd',
            'filesize': filesize,
            'url': video_url,
        }]

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }
