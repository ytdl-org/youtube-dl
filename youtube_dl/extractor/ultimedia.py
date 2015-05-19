# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_urllib_parse_urlparse
from ..utils import (
    ExtractorError,
    qualities,
    unified_strdate,
    clean_html,
)


class UltimediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ultimedia\.com/default/index/video[^/]+/id/(?P<id>[\d+a-z]+)'
    _TESTS = [{
        # news
        'url': 'https://www.ultimedia.com/default/index/videogeneric/id/s8uk0r',
        'md5': '276a0e49de58c7e85d32b057837952a2',
        'info_dict': {
            'id': 's8uk0r',
            'ext': 'mp4',
            'title': 'Loi sur la fin de vie: le texte prévoit un renforcement des directives anticipées',
            'description': 'md5:3e5c8fd65791487333dda5db8aed32af',
            'thumbnail': 're:^https?://.*\.jpg',
            'upload_date': '20150317',
        },
    }, {
        # music
        'url': 'https://www.ultimedia.com/default/index/videomusic/id/xvpfp8',
        'md5': '2ea3513813cf230605c7e2ffe7eca61c',
        'info_dict': {
            'id': 'xvpfp8',
            'ext': 'mp4',
            'title': "Two - C'est la vie (Clip)",
            'description': 'Two',
            'thumbnail': 're:^https?://.*\.jpg',
            'upload_date': '20150224',
        },
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        deliver_url = self._proto_relative_url(self._search_regex(
            r'<iframe[^>]+src="((?:https?:)?//(?:www\.)?ultimedia\.com/deliver/[^"]+)"',
            webpage, 'deliver URL'), compat_urllib_parse_urlparse(url).scheme + ':')

        deliver_page = self._download_webpage(
            deliver_url, video_id, 'Downloading iframe page')

        if '>This video is currently not available' in deliver_page:
            raise ExtractorError(
                'Video %s is currently not available' % video_id, expected=True)

        player = self._parse_json(
            self._search_regex(
                r"jwplayer\('player(?:_temp)?'\)\.setup\(({.+?})\)\.on",
                deliver_page, 'player'),
            video_id)

        quality = qualities(['flash', 'html5'])
        formats = []
        for mode in player['modes']:
            video_url = mode.get('config', {}).get('file')
            if not video_url:
                continue
            if re.match(r'https?://www\.youtube\.com/.+?', video_url):
                return self.url_result(video_url, 'Youtube')
            formats.append({
                'url': video_url,
                'format_id': mode.get('type'),
                'quality': quality(mode.get('type')),
            })
        self._sort_formats(formats)

        thumbnail = player.get('image')

        title = clean_html((
            self._html_search_regex(
                r'(?s)<div\s+id="catArticle">.+?</div>(.+?)</h1>',
                webpage, 'title', default=None) or
            self._search_regex(
                r"var\s+nameVideo\s*=\s*'([^']+)'",
                deliver_page, 'title')))

        description = clean_html(self._html_search_regex(
            r'(?s)<span>Description</span>(.+?)</p>', webpage,
            'description', fatal=False))

        upload_date = unified_strdate(self._search_regex(
            r'Ajouté le\s*<span>([^<]+)', webpage,
            'upload date', fatal=False))

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'upload_date': upload_date,
            'formats': formats,
        }
