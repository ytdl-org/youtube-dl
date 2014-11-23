from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    compat_urllib_request,
    parse_duration,
    str_to_int,
)


class XTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>xtube\.com/watch\.php\?v=(?P<videoid>[^/?&]+))'
    _TEST = {
        'url': 'http://www.xtube.com/watch.php?v=kVTUy_G222_',
        'md5': '092fbdd3cbe292c920ef6fc6a8a9cdab',
        'info_dict': {
            'id': 'kVTUy_G222_',
            'ext': 'mp4',
            'title': 'strange erotica',
            'description': 'http://www.xtube.com an ET kind of thing',
            'uploader': 'greenshowers',
            'duration': 450,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')
        url = 'http://www.' + mobj.group('url')

        req = compat_urllib_request.Request(url)
        req.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(req, video_id)

        video_title = self._html_search_regex(r'<p class="title">([^<]+)', webpage, 'title')
        video_uploader = self._html_search_regex(
            r'so_s\.addVariable\("owner_u", "([^"]+)', webpage, 'uploader', fatal=False)
        video_description = self._html_search_regex(
            r'<p class="fieldsDesc">([^<]+)', webpage, 'description', fatal=False)
        duration = parse_duration(self._html_search_regex(
            r'<span class="bold">Runtime:</span> ([^<]+)</p>', webpage, 'duration', fatal=False))
        view_count = self._html_search_regex(
            r'<span class="bold">Views:</span> ([\d,\.]+)</p>', webpage, 'view count', fatal=False)
        if view_count:
            view_count = str_to_int(view_count)
        comment_count = self._html_search_regex(
            r'<div id="commentBar">([\d,\.]+) Comments</div>', webpage, 'comment count', fatal=False)
        if comment_count:
            comment_count = str_to_int(comment_count)

        player_quality_option = json.loads(self._html_search_regex(
            r'playerQualityOption = ({.+?});', webpage, 'player quality option'))

        QUALITIES = ['3gp', 'mp4_normal', 'mp4_high', 'flv', 'mp4_ultra', 'mp4_720', 'mp4_1080']
        formats = [
            {
                'url': furl,
                'format_id': format_id,
                'preference': QUALITIES.index(format_id) if format_id in QUALITIES else -1,
            } for format_id, furl in player_quality_option.items()
        ]
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
            'entries': [{
                '_type': 'url',
                'url': eurl,
                'ie_key': 'XTube',
            } for eurl in urls]
        }
