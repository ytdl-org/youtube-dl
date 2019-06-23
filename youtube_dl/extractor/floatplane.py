# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, urlencode_postdata, try_get, int_or_none
from ..compat import compat_str


class FloatplaneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?floatplane\.com/video/(?P<id>[A-Za-z0-9]+)'
    _NETRC_MACHINE = 'floatplane'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        username, password = self._get_login_info()
        try:
            request_data = urlencode_postdata({
                'username': username,
                'password': password
            })
            user_json = self._download_json('https://www.floatplane.com/api/auth/login', video_id, data=request_data, note='Logging in')
            self.to_screen('Logged in as %s.' % user_json['user']['username'])
            # What if url_json['user']['needs2FA']? Can we ask for token from ytdl?
            # Post 'token' to https://www.floatplane.com/api/auth/checkFor2faLogin
        except ExtractorError as e:
            # Will cause 401 if password isn't accepted
            print(e)
            raise ExtractorError('Floatplane login error! Check your .netrc for correct login/password.', expected=True)

        try:
            info_json = self._download_json('https://www.floatplane.com/api/video/info?videoGUID=%s' % video_id, video_id, note='Downloading video info')
        except ExtractorError as e:
            print(e)
            raise ExtractorError('Floatplane download error! Please make sure you\'re logged in.', expected=True)

        formats = []
        # unfortunately it needs to download video url for each quality
        #   so I have to download 4 pages each time
        for level in info_json['levels']:
            video_url = self._download_webpage('https://www.floatplane.com/api/video/url?guid=%s&quality=%s' % (video_id, level['name']), video_id, note='Downloading url for %s' % level['label'])
            video_url = video_url.strip('"')
            formats.append({
                'format_id': level['name'],
                'url': video_url,
                'quality': level.get('label'),
                'width': level.get('width'),
                'height': level.get('height')
            })

        return {
            'id': video_id,
            'title': info_json['title'],
            'description': info_json.get('description'),
            'url': video_url,
            'thumbnail': try_get(info_json, lambda x: x['thumbnail']['path'], compat_str),
            'formats': formats,
            'duration': int_or_none(info_json.get('duration'))
        }
