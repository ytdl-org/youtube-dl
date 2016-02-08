from __future__ import unicode_literals

import itertools
import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_unquote
from ..utils import (
    int_or_none,
    parse_duration,
    sanitized_Request,
    str_to_int,
)


class XTubeIE(InfoExtractor):
    _VALID_URL = r'(?:xtube:|https?://(?:www\.)?xtube\.com/watch\.php\?.*\bv=)(?P<id>[^/?&#]+)'
    _TEST = {
        'url': 'http://www.xtube.com/watch.php?v=kVTUy_G222_',
        'md5': '092fbdd3cbe292c920ef6fc6a8a9cdab',
        'info_dict': {
            'id': 'kVTUy_G222_',
            'ext': 'mp4',
            'title': 'strange erotica',
            'description': 'contains:an ET kind of thing',
            'uploader': 'greenshowers',
            'duration': 450,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        req = sanitized_Request('http://www.xtube.com/watch.php?v=%s' % video_id)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(
            r'<p class="title">([^<]+)', webpage, 'title')
        video_uploader = self._html_search_regex(
            [r"var\s+contentOwnerId\s*=\s*'([^']+)",
             r'By:\s*<a href="/community/profile\.php\?user=([^"]+)'],
            webpage, 'uploader', fatal=False)
        video_description = self._html_search_regex(
            r'<p class="fieldsDesc">([^<]+)',
            webpage, 'description', fatal=False)
        duration = parse_duration(self._html_search_regex(
            r'<span class="bold">Runtime:</span> ([^<]+)</p>',
            webpage, 'duration', fatal=False))
        view_count = str_to_int(self._html_search_regex(
            r'<span class="bold">Views:</span> ([\d,\.]+)</p>',
            webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._html_search_regex(
            r'<div id="commentBar">([\d,\.]+) Comments</div>',
            webpage, 'comment count', fatal=False))

        formats = []
        for format_id, video_url in re.findall(
                r'flashvars\.quality_(.+?)\s*=\s*"([^"]+)"', webpage):
            fmt = {
                'url': compat_urllib_parse_unquote(video_url),
                'format_id': format_id,
            }
            m = re.search(r'^(?P<height>\d+)[pP]', format_id)
            if m:
                fmt['height'] = int(m.group('height'))
            formats.append(fmt)

        if not formats:
            video_url = compat_urllib_parse_unquote(self._search_regex(
                r'flashvars\.video_url\s*=\s*"([^"]+)"',
                webpage, 'video URL'))
            formats.append({'url': video_url})

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': video_title,
            'uploader': video_uploader,
            'description': video_description,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
        }


class XTubeUserIE(InfoExtractor):
    IE_DESC = 'XTube user profile'
    _VALID_URL = r'https?://(?:www\.)?xtube\.com/profile/(?P<id>[^/]+-\d+)'
    _TEST = {
        'url': 'http://www.xtube.com/profile/greenshowers-4056496',
        'info_dict': {
            'id': 'greenshowers-4056496',
            'age_limit': 18,
        },
        'playlist_mincount': 155,
    }

    def _real_extract(self, url):
        user_id = self._match_id(url)

        entries = []
        for pagenum in itertools.count(1):
            request = sanitized_Request(
                'http://www.xtube.com/profile/%s/videos/%d' % (user_id, pagenum),
                headers={
                    'Cookie': 'popunder=4',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': url,
                })

            page = self._download_json(
                request, user_id, 'Downloading videos JSON page %d' % pagenum)

            html = page.get('html')
            if not html:
                break

            for _, video_id in re.findall(r'data-plid=(["\'])(.+?)\1', html):
                entries.append(self.url_result('xtube:%s' % video_id, XTubeIE.ie_key()))

            page_count = int_or_none(page.get('pageCount'))
            if not page_count or pagenum == page_count:
                break

        playlist = self.playlist_result(entries, user_id)
        playlist['age_limit'] = 18
        return playlist
