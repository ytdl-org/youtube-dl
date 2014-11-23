from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    unified_strdate,
    str_to_int,
    parse_duration,
    clean_html,
)


class FourTubeIE(InfoExtractor):
    IE_NAME = '4tube'
    _VALID_URL = r'https?://(?:www\.)?4tube\.com/videos/(?P<id>\d+)'

    _TEST = {
        'url': 'http://www.4tube.com/videos/209733/hot-babe-holly-michaels-gets-her-ass-stuffed-by-black',
        'md5': '6516c8ac63b03de06bc8eac14362db4f',
        'info_dict': {
            'id': '209733',
            'ext': 'mp4',
            'title': 'Hot Babe Holly Michaels gets her ass stuffed by black',
            'uploader': 'WCP Club',
            'uploader_id': 'wcp-club',
            'upload_date': '20131031',
            'duration': 583,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        webpage_url = 'http://www.4tube.com/videos/' + video_id
        webpage = self._download_webpage(webpage_url, video_id)

        self.report_extraction(video_id)

        playlist_json = self._html_search_regex(r'var playerConfigPlaylist\s+=\s+([^;]+)', webpage, 'Playlist')
        media_id = self._search_regex(r'idMedia:\s*(\d+)', playlist_json, 'Media Id')
        sources = self._search_regex(r'sources:\s*\[([^\]]*)\]', playlist_json, 'Sources').split(',')
        title = self._search_regex(r'title:\s*"([^"]*)', playlist_json, 'Title')
        thumbnail_url = self._search_regex(r'image:\s*"([^"]*)', playlist_json, 'Thumbnail', fatal=False)

        uploader_str = self._search_regex(r'<span>Uploaded by</span>(.*?)<span>', webpage, 'uploader', fatal=False)
        mobj = re.search(r'<a href="/sites/(?P<id>[^"]+)"><strong>(?P<name>[^<]+)</strong></a>', uploader_str)
        (uploader, uploader_id) = (mobj.group('name'), mobj.group('id')) if mobj else (clean_html(uploader_str), None)

        upload_date = None
        view_count = None
        duration = None
        description = self._html_search_meta('description', webpage, 'description')
        if description:
            upload_date = self._search_regex(r'Published Date: (\d{2} [a-zA-Z]{3} \d{4})', description, 'upload date',
                                             fatal=False)
            if upload_date:
                upload_date = unified_strdate(upload_date)
            view_count = self._search_regex(r'Views: ([\d,\.]+)', description, 'view count', fatal=False)
            if view_count:
                view_count = str_to_int(view_count)
            duration = parse_duration(self._search_regex(r'Length: (\d+m\d+s)', description, 'duration', fatal=False))

        token_url = "http://tkn.4tube.com/{0}/desktop/{1}".format(media_id, "+".join(sources))
        headers = {
            b'Content-Type': b'application/x-www-form-urlencoded',
            b'Origin': b'http://www.4tube.com',
        }
        token_req = compat_urllib_request.Request(token_url, b'{}', headers)
        tokens = self._download_json(token_req, video_id)

        formats = [{
            'url': tokens[format]['token'],
            'format_id': format + 'p',
            'resolution': format + 'p',
            'quality': int(format),
        } for format in sources]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'thumbnail': thumbnail_url,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'upload_date': upload_date,
            'view_count': view_count,
            'duration': duration,
            'age_limit': 18,
            'webpage_url': webpage_url,
        }
