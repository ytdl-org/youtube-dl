from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    compat_urllib_parse,
)


class MooshareIE(InfoExtractor):
    IE_NAME = 'mooshare'
    IE_DESC = 'Mooshare.biz'
    _VALID_URL = r'http://mooshare\.biz/(?P<id>[\da-z]{12})'

    _TESTS = [
        {
            'url': 'http://mooshare.biz/8dqtk4bjbp8g',
            'md5': '4e14f9562928aecd2e42c6f341c8feba',
            'info_dict': {
                'id': '8dqtk4bjbp8g',
                'ext': 'mp4',
                'title': 'Comedy Football 2011 - (part 1-2)',
                'duration': 893,
            },
        },
        {
            'url': 'http://mooshare.biz/aipjtoc4g95j',
            'info_dict': {
                'id': 'aipjtoc4g95j',
                'ext': 'mp4',
                'title': 'Orange Caramel  Dashing Through the Snow',
                'duration': 212,
            },
            'params': {
                # rtmp download
                'skip_download': True,
            }
        }
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        page = self._download_webpage(url, video_id, 'Downloading page')

        if re.search(r'>Video Not Found or Deleted<', page) is not None:
            raise ExtractorError(u'Video %s does not exist' % video_id, expected=True)

        hash_key = self._html_search_regex(r'<input type="hidden" name="hash" value="([^"]+)">', page, 'hash')
        title = self._html_search_regex(r'(?m)<div class="blockTitle">\s*<h2>Watch ([^<]+)</h2>', page, 'title')

        download_form = {
            'op': 'download1',
            'id': video_id,
            'hash': hash_key,
        }

        request = compat_urllib_request.Request(
            'http://mooshare.biz/%s' % video_id, compat_urllib_parse.urlencode(download_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')

        self.to_screen('%s: Waiting for timeout' % video_id)
        time.sleep(5)

        video_page = self._download_webpage(request, video_id, 'Downloading video page')

        thumbnail = self._html_search_regex(r'image:\s*"([^"]+)",', video_page, 'thumbnail', fatal=False)
        duration_str = self._html_search_regex(r'duration:\s*"(\d+)",', video_page, 'duration', fatal=False)
        duration = int(duration_str) if duration_str is not None else None

        formats = []

        # SD video
        mobj = re.search(r'(?m)file:\s*"(?P<url>[^"]+)",\s*provider:', video_page)
        if mobj is not None:
            formats.append({
                'url': mobj.group('url'),
                'format_id': 'sd',
                'format': 'SD',
            })

        # HD video
        mobj = re.search(r'\'hd-2\': { file: \'(?P<url>[^\']+)\' },', video_page)
        if mobj is not None:
            formats.append({
                'url': mobj.group('url'),
                'format_id': 'hd',
                'format': 'HD',
            })

        # rtmp video
        mobj = re.search(r'(?m)file: "(?P<playpath>[^"]+)",\s*streamer: "(?P<rtmpurl>rtmp://[^"]+)",', video_page)
        if mobj is not None:
            formats.append({
                'url': mobj.group('rtmpurl'),
                'play_path': mobj.group('playpath'),
                'rtmp_live': False,
                'ext': 'mp4',
                'format_id': 'rtmp',
                'format': 'HD',
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }