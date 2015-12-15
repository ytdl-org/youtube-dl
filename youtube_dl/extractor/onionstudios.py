# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import determine_ext


class OnionStudiosIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?onionstudios\.com/(?:videos/[^/]+-|embed\?.*\bid=)(?P<id>\d+)(?!-)'

    _TESTS = [{
        'url': 'http://www.onionstudios.com/videos/hannibal-charges-forward-stops-for-a-cocktail-2937',
        'md5': 'd4851405d31adfadf71cd7a487b765bb',
        'info_dict': {
            'id': '2937',
            'ext': 'mp4',
            'title': 'Hannibal charges forward, stops for a cocktail',
            'description': 'md5:545299bda6abf87e5ec666548c6a9448',
            'thumbnail': 're:^https?://.*\.jpg$',
            'uploader': 'The A.V. Club',
            'uploader_id': 'TheAVClub',
        },
    }, {
        'url': 'http://www.onionstudios.com/embed?id=2855&autoplay=true',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+?src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?onionstudios\.com/embed.+?)\1', webpage)
        if mobj:
            return mobj.group('url')

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.onionstudios.com/embed?id=%s' % video_id, video_id)

        formats = []
        for src in re.findall(r'<source[^>]+src="([^"]+)"', webpage):
            if determine_ext(src) != 'm3u8':  # m3u8 always results in 403
                formats.append({
                    'url': src,
                })
        self._sort_formats(formats)

        title = self._search_regex(
            r'share_title\s*=\s*(["\'])(?P<title>[^\1]+?)\1',
            webpage, 'title', group='title')
        description = self._search_regex(
            r'share_description\s*=\s*(["\'])(?P<description>[^\1]+?)\1',
            webpage, 'description', default=None, group='description')
        thumbnail = self._search_regex(
            r'poster\s*=\s*(["\'])(?P<thumbnail>[^\1]+?)\1',
            webpage, 'thumbnail', default=False, group='thumbnail')

        uploader_id = self._search_regex(
            r'twitter_handle\s*=\s*(["\'])(?P<uploader_id>[^\1]+?)\1',
            webpage, 'uploader id', fatal=False, group='uploader_id')
        uploader = self._search_regex(
            r'window\.channelName\s*=\s*(["\'])Embedded:(?P<uploader>[^\1]+?)\1',
            webpage, 'uploader', default=False, group='uploader')

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'formats': formats,
        }
