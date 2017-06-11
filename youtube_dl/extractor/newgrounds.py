from __future__ import unicode_literals

from .common import InfoExtractor
import re

class NewgroundsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?newgrounds\.com/(?:audio/listen|portal/view)/(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'https://www.newgrounds.com/audio/listen/549479',
        'md5': 'fe6033d297591288fa1c1f780386f07a',
        'info_dict': {
            'id': '549479',
            'ext': 'mp3',
            'title': 'B7 - BusMode',
            'uploader': 'Burn7',
            'upload_date': '20130911',
            'duration': 143
        }
    }, {
        'url': 'https://www.newgrounds.com/portal/view/673111',
        'md5': '3394735822aab2478c31b1004fe5e5bc',
        'info_dict': {
            'id': '673111',
            'ext': 'mp4',
            'title': 'Dancin',
            'uploader': 'Squirrelman82',
        },
    }]

    def _real_extract(self, url):
        media_id = self._match_id(url)
        webpage = self._download_webpage(url, media_id)

        title = self._html_search_regex(
            r'<title>([^>]+)</title>', webpage, 'title')

        uploader = self._html_search_regex(
            r'Author\s*<a[^>]+>([^<]+)', webpage, 'uploader', fatal=False)

        music_url = self._parse_json(self._search_regex(
            r'"url":("[^"]+"),', webpage, ''), media_id)
        
        match = re.search(
            (r'"sidestats">\s*<dt>Uploaded</dt>\s*<dd>(.+?)<dd>\s'
             r'<dt.*?<dd>([a-z0-9 ]+)</dd>\s<dt>Score'), webpage)
        
        ret_data = {
            'id': media_id,
            'title': title,
            'url': music_url,
            'uploader': uploader,
        }
        
        if match is not None:
            uploaded_at, length = match.groups()

            date = datetime.datetime.strptime(uploaded_at, "%b %m, %Y | %I:%M %p %Z")

            ret_data["upload_date"] = date.strftime("%Y%m%d")
            
            fmt = "%H hrs %M min %S sec"

            duration = None

            while duration is None:
                try:
                    duration = datetime.datetime.strptime(length, fmt)
                except ValueError:
                    fmt = fmt[7:]
            
            ret_data["duration"] = duration

        return ret_data
