from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_request,
    compat_urllib_parse_unquote,
)
from ..utils import (
    parse_duration,
    str_to_int,
)


class XTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>xtube\.com/watch\.php\?v=(?P<id>[^/?&#]+))'
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

        req = compat_urllib_request.Request(url)
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
    _VALID_URL = r'https?://(?:www\.)?xtube\.com/community/profile\.php\?(.*?)user=(?P<username>[^&#]+)(?:$|[&#])'
    _TEST = {
        'url': 'http://www.xtube.com/community/profile.php?user=greenshowers',
        'info_dict': {
            'id': 'greenshowers',
            'age_limit': 18,
        },
        'playlist_mincount': 155,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        username = mobj.group('username')

        profile_page = self._download_webpage(
            url, username, note='Retrieving profile page')

        video_count = int(self._search_regex(
            r'<strong>%s\'s Videos \(([0-9]+)\)</strong>' % username, profile_page,
            'video count'))

        PAGE_SIZE = 25
        urls = []
        page_count = (video_count + PAGE_SIZE + 1) // PAGE_SIZE
        for n in range(1, page_count + 1):
            lpage_url = 'http://www.xtube.com/user_videos.php?page=%d&u=%s' % (n, username)
            lpage = self._download_webpage(
                lpage_url, username,
                note='Downloading page %d/%d' % (n, page_count))
            urls.extend(
                re.findall(r'addthis:url="([^"]+)"', lpage))

        return {
            '_type': 'playlist',
            'id': username,
            'age_limit': 18,
            'entries': [{
                '_type': 'url',
                'url': eurl,
                'ie_key': 'XTube',
            } for eurl in urls]
        }
