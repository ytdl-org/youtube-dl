# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import ExtractorError, urlencode_postdata, try_get, int_or_none
from ..compat import compat_str


class FloatplaneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?floatplane\.com/post/(?P<id>[A-Za-z0-9]+)'
    _NETRC_MACHINE = 'floatplane'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        username, password = self._get_login_info()
        try:
            request_data = urlencode_postdata({
                'username': username,
                'password': password
            })
            user_json = self._download_json('https://www.floatplane.com/api/v2/auth/login', video_id, data=request_data, note='Logging in')
            self.to_screen('Logged in as %s.' % user_json['user']['username'])
            # What if url_json['user']['needs2FA']? Can we ask for token from ytdl?
            # Post 'token' to https://www.floatplane.com/api/auth/checkFor2faLogin
        except ExtractorError as e:
            # Will cause 401 if password isn't accepted
            print(e)
            raise ExtractorError('Floatplane login error! Check your .netrc for correct login/password.', expected=True)

        try:
            info_json = self._download_json('https://www.floatplane.com/api/v3/content/post?id=%s' % video_id, video_id, note='Downloading video info')
        except ExtractorError as e:
            print(e)
            raise ExtractorError('Floatplane download error! Please make sure you\'re logged in.', expected=True)

        attachments = info_json.get('attachmentOrder')
        if not attachments or len(attachments) < 1:
            raise ExtractorError('Can\'t get real video id!')
        # I'm guessing this is for future addition of playlists, but currently
        #  a "post" always contains a single video
        real_video_id = attachments[0]
        if self._downloader.params.get('verbose', False):
            self.to_screen('Real video id: %s.' % real_video_id)

        try:
            cdn_json = self._download_json('https://www.floatplane.com/api/v2/cdn/delivery?type=vod&guid=%s' % real_video_id, video_id, note='Downloading delivery info')
        except ExtractorError as e:
            print(e)
            raise ExtractorError('Floatplane download error! Please make sure you\'re logged in.', expected=True)

        formats = []
        # new api has all the info in one request, no more downloading
        #  each url separately
        for level in cdn_json['resource']['data']['qualityLevels']:
            video_url = cdn_json['cdn'] + cdn_json['resource']['uri']
            video_url = video_url.replace('{qualityLevels}',level['name'])
            video_url = video_url.replace('{qualityLevelParams.token}',cdn_json['resource']['data']['qualityLevelParams'][level['name']]['token'])
            formats.append({
                'format_id': level['name'],
                'url': video_url,
                'quality': level.get('label'),
                'width': level.get('width'),
                'height': level.get('height'),
                'ext': 'mp4'
                # with delivery?type=download, extension is mp4, but we want
                #  to keep using the vod api (worked when downloads didn't)
            })

        return {
            'id': video_id,
            'title': info_json['title'],
            'description': info_json.get('description'),
            'url': video_url,
            'thumbnail': try_get(info_json, lambda x: x['thumbnail']['path'], compat_str),
            'formats': formats,
            'duration': int_or_none(try_get(info_json, lambda x: x['metsadata']['videoDuration']))
        }
