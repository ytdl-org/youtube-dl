from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
)
from ..utils import (
    ExtractorError,
    HEADRequest,
    str_to_int,
    parse_iso8601,
)


class MixcloudIE(InfoExtractor):
    _VALID_URL = r'^(?:https?://)?(?:www\.)?mixcloud\.com/([^/]+)/([^/]+)'
    IE_NAME = 'mixcloud'

    _TESTS = [{
        'url': 'http://www.mixcloud.com/dholbach/cryptkeeper/',
        'info_dict': {
            'id': 'dholbach-cryptkeeper',
            'ext': 'mp3',
            'title': 'Cryptkeeper',
            'description': 'After quite a long silence from myself, finally another Drum\'n\'Bass mix with my favourite current dance floor bangers.',
            'uploader': 'Daniel Holbach',
            'uploader_id': 'dholbach',
            'upload_date': '20111115',
            'timestamp': 1321359578,
            'thumbnail': 're:https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
        },
    }, {
        'url': 'http://www.mixcloud.com/gillespeterson/caribou-7-inch-vinyl-mix-chat/',
        'info_dict': {
            'id': 'gillespeterson-caribou-7-inch-vinyl-mix-chat',
            'ext': 'm4a',
            'title': 'Electric Relaxation vol. 3',
            'description': 'md5:2b8aec6adce69f9d41724647c65875e8',
            'uploader': 'Daniel Drumz',
            'uploader_id': 'gillespeterson',
            'thumbnail': 're:https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
        },
    }]

    def _get_url(self, track_id, template_url):
        server_count = 30
        for i in range(server_count):
            url = template_url % i
            try:
                # We only want to know if the request succeed
                # don't download the whole file
                self._request_webpage(
                    HEADRequest(url), track_id,
                    'Checking URL %d/%d ...' % (i + 1, server_count + 1))
                return url
            except ExtractorError:
                pass

        return None

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group(1)
        cloudcast_name = mobj.group(2)
        track_id = compat_urllib_parse.unquote('-'.join((uploader, cloudcast_name)))

        webpage = self._download_webpage(url, track_id)

        preview_url = self._search_regex(
            r'\s(?:data-preview-url|m-preview)="([^"]+)"', webpage, 'preview url')
        song_url = preview_url.replace('/previews/', '/c/originals/')
        template_url = re.sub(r'(stream\d*)', 'stream%d', song_url)
        final_song_url = self._get_url(track_id, template_url)
        if final_song_url is None:
            self.to_screen('Trying with m4a extension')
            template_url = template_url.replace('.mp3', '.m4a').replace('originals/', 'm4a/64/')
            final_song_url = self._get_url(track_id, template_url)
        if final_song_url is None:
            raise ExtractorError('Unable to extract track url')

        PREFIX = (
            r'<span class="play-button[^"]*?"'
            r'(?:\s+[a-zA-Z0-9-]+(?:="[^"]+")?)*?\s+')
        title = self._html_search_regex(
            PREFIX + r'm-title="([^"]+)"', webpage, 'title')
        thumbnail = self._proto_relative_url(self._html_search_regex(
            PREFIX + r'm-thumbnail-url="([^"]+)"', webpage, 'thumbnail',
            fatal=False))
        uploader = self._html_search_regex(
            PREFIX + r'm-owner-name="([^"]+)"',
            webpage, 'uploader', fatal=False)
        uploader_id = self._search_regex(
            r'\s+"profile": "([^"]+)",', webpage, 'uploader id', fatal=False)
        description = self._og_search_description(webpage)
        like_count = str_to_int(self._search_regex(
            [r'<meta itemprop="interactionCount" content="UserLikes:([0-9]+)"',
             r'/favorites/?">([0-9]+)<'],
            webpage, 'like count', fatal=False))
        view_count = str_to_int(self._search_regex(
            [r'<meta itemprop="interactionCount" content="UserPlays:([0-9]+)"',
             r'/listeners/?">([0-9,.]+)</a>'],
            webpage, 'play count', fatal=False))
        timestamp = parse_iso8601(self._search_regex(
            r'<time itemprop="dateCreated" datetime="([^"]+)">',
            webpage, 'upload date', default=None))

        return {
            'id': track_id,
            'title': title,
            'url': final_song_url,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': like_count,
        }
