# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .kaltura import KalturaIE
from ..utils import (
    extract_attributes,
    remove_end,
    urlencode_postdata,
)


class AsianCrushIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?asiancrush\.com/video/(?:[^/]+/)?0+(?P<id>\d+)v\b'
    _TESTS = [{
        'url': 'https://www.asiancrush.com/video/012869v/women-who-flirt/',
        'md5': 'c3b740e48d0ba002a42c0b72857beae6',
        'info_dict': {
            'id': '1_y4tmjm5r',
            'ext': 'mp4',
            'title': 'Women Who Flirt',
            'description': 'md5:3db14e9186197857e7063522cb89a805',
            'timestamp': 1496936429,
            'upload_date': '20170608',
            'uploader_id': 'craig@crifkin.com',
        },
    }, {
        'url': 'https://www.asiancrush.com/video/she-was-pretty/011886v-pretty-episode-3/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'https://www.asiancrush.com/wp-admin/admin-ajax.php', video_id,
            data=urlencode_postdata({
                'postid': video_id,
                'action': 'get_channel_kaltura_vars',
            }))

        entry_id = data['entry_id']

        return self.url_result(
            'kaltura:%s:%s' % (data['partner_id'], entry_id),
            ie=KalturaIE.ie_key(), video_id=entry_id,
            video_title=data.get('vid_label'))


class AsianCrushPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?asiancrush\.com/series/0+(?P<id>\d+)s\b'
    _TEST = {
        'url': 'https://www.asiancrush.com/series/012481s/scholar-walks-night/',
        'info_dict': {
            'id': '12481',
            'title': 'Scholar Who Walks the Night',
            'description': 'md5:7addd7c5132a09fd4741152d96cce886',
        },
        'playlist_count': 20,
    }

    def _real_extract(self, url):
        playlist_id = self._match_id(url)

        webpage = self._download_webpage(url, playlist_id)

        entries = []

        for mobj in re.finditer(
                r'<a[^>]+href=(["\'])(?P<url>%s.*?)\1[^>]*>' % AsianCrushIE._VALID_URL,
                webpage):
            attrs = extract_attributes(mobj.group(0))
            if attrs.get('class') == 'clearfix':
                entries.append(self.url_result(
                    mobj.group('url'), ie=AsianCrushIE.ie_key()))

        title = remove_end(
            self._html_search_regex(
                r'(?s)<h1\b[^>]\bid=["\']movieTitle[^>]+>(.+?)</h1>', webpage,
                'title', default=None) or self._og_search_title(
                webpage, default=None) or self._html_search_meta(
                'twitter:title', webpage, 'title',
                default=None) or self._search_regex(
                r'<title>([^<]+)</title>', webpage, 'title', fatal=False),
            ' | AsianCrush')

        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage, 'description', fatal=False)

        return self.playlist_result(entries, playlist_id, title, description)
