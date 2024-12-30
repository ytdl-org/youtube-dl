from __future__ import unicode_literals

import json
import re
from .common import (
    InfoExtractor,
    RegexNotFoundError,
)
from ..utils import (
    clean_html,
    compat_str,
    js_to_json,
    urljoin,
    try_get,
)


class Keep2ShareIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:k2s\.cc|keep2share\.cc|keep2share\.com)/file/(?P<id>[^/?#]+)'
    _TESTS = [{
        'url': 'https://k2s.cc/file/d6f565bcb9581/Big_Buck%20Bunny%20Trailer.mp4',
        'md5': '0dbce91e7d1efc506d1461439eb8a4c0',
        'info_dict': {
            'id': 'd6f565bcb9581',
            'ext': 'mp4',
            'title': 'Big Buck Bunny Trailer.mp4',
            'thumbnail': r're:^https?://.*\.jpe?g$',
            'filesize': 4447915,
            'duration': 33.019,
        },
    }]

    def _get_app_secret(self, video_id):
        """ retrieve REACT_APP_API_CLIENT_SECRET """

        if getattr(self, '_app_secret', None) is not None:
            return self._app_secret

        url = 'https://k2s.cc/file/' + video_id
        webpage = self._download_webpage(url, video_id)
        scripts = re.finditer(r'<script\s+src="(?P<src>/static/[^"]*)"', webpage)
        for mobj in scripts:
            src = urljoin(url, clean_html(mobj.group('src')))
            script = self._download_webpage(src, video_id)
            secret = self._search_regex(
                r'REACT_APP_API_CLIENT_SECRET:\s*(?P<secret>%(string)s)' % {
                    'string': r'"(?:[^"]|\\")*"' + '|' + r"'(?:[^']|\\')*'",
                }, script, 'app secret', group='secret', default=None)
            if secret is not None:
                self._app_secret = self._parse_json(secret, video_id,
                                                    transform_source=js_to_json)
                return self._app_secret

        raise RegexNotFoundError('Unable to extract app secret')

    def _get_access_token(self, video_id):
        """ retrieve access_token """

        if getattr(self, '_access_token', None) is not None:
            return self._access_token

        data = {
            'grant_type': 'client_credentials',
            'client_id': 'k2s_web_app',
            'client_secret': self._get_app_secret(video_id),
        }
        data = json.dumps(data, separators=(',', ':')).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        tokens = self._download_json('https://api.k2s.cc/v1/auth/token',
                                     video_id, data=data, headers=headers)
        self._access_token = tokens['access_token']

        return self._access_token

    def _real_extract(self, url):
        video_id = self._match_id(url)

        headers = {'Cookie': 'accessToken=' + self._get_access_token(url)}
        info = self._download_json('https://api.k2s.cc/v1/files/' + video_id,
                                   video_id, headers=headers)

        return {
            'id': video_id,
            'title': info.get('name', 'keep2share-file'),
            'thumbnail': try_get(info, lambda x: x['videoPreview']['cover'], compat_str),
            'duration': try_get(info, lambda x: x['videoInfo']['duration'], (int, float)),
            'formats': [{
                'url': info['videoPreview']['video'],
                'ext': 'mp4',
                'filesize': try_get(info, lambda x: x['size'], int),
                'width': try_get(info, lambda x: x['videoInfo']['resolution']['width'], int),
                'height': try_get(info, lambda x: x['videoInfo']['resolution']['height'], int),
            }],
        }
