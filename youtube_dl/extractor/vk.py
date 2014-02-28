# encoding: utf-8
from __future__ import unicode_literals

import re
import json

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_urllib_request,
    compat_urllib_parse,
    compat_str,
    unescapeHTML,
)


class VKIE(InfoExtractor):
    IE_NAME = 'vk.com'
    _VALID_URL = r'https?://vk\.com/(?:video_ext\.php\?.*?\boid=(?P<oid>\d+).*?\bid=(?P<id>\d+)|(?:videos.*?\?.*?z=)?video(?P<videoid>.*?)(?:\?|%2F|$))'
    _NETRC_MACHINE = 'vk'

    _TESTS = [
        {
            'url': 'http://vk.com/videos-77521?z=video-77521_162222515%2Fclub77521',
            'md5': '0deae91935c54e00003c2a00646315f0',
            'info_dict': {
                'id': '162222515',
                'ext': 'flv',
                'title': 'ProtivoGunz - Хуёвая песня',
                'uploader': 'Noize MC',
                'duration': 195,
            },
        },
        {
            'url': 'http://vk.com/video4643923_163339118',
            'md5': 'f79bccb5cd182b1f43502ca5685b2b36',
            'info_dict': {
                'id': '163339118',
                'ext': 'mp4',
                'uploader': 'Elvira Dzhonik',
                'title': 'Dream Theater - Hollow Years Live at Budokan 720*',
                'duration': 558,
            }
        },
        {
            'note': 'Embedded video',
            'url': 'http://vk.com/video_ext.php?oid=32194266&id=162925554&hash=7d8c2e0d5e05aeaa&hd=1',
            'md5': 'c7ce8f1f87bec05b3de07fdeafe21a0a',
            'info_dict': {
                'id': '162925554',
                'ext': 'mp4',
                'uploader': 'Vladimir Gavrin',
                'title': 'Lin Dan',
                'duration': 101,
            }
        },
        {
            'url': 'http://vk.com/video-8871596_164049491',
            'md5': 'a590bcaf3d543576c9bd162812387666',
            'note': 'Only available for registered users',
            'info_dict': {
                'id': '164049491',
                'ext': 'mp4',
                'uploader': 'Триллеры',
                'title': '► Бойцовский клуб / Fight Club 1999 [HD 720]\u00a0',
                'duration': 8352,
            },
            'skip': 'Requires vk account credentials',
        },
    ]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'act': 'login',
            'role': 'al_frame',
            'expire': '1',
            'email': username,
            'pass': password,
        }

        request = compat_urllib_request.Request('https://login.vk.com/?act=login',
            compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        login_page = self._download_webpage(request, None, note='Logging in as %s' % username)

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError('Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('videoid')

        if not video_id:
            video_id = '%s_%s' % (mobj.group('oid'), mobj.group('id'))

        info_url = 'http://vk.com/al_video.php?act=show&al=1&video=%s' % video_id
        info_page = self._download_webpage(info_url, video_id)

        if re.search(r'<!>Please log in or <', info_page):
            raise ExtractorError('This video is only available for registered users, '
                'use --username and --password options to provide account credentials.', expected=True)

        m_yt = re.search(r'src="(http://www.youtube.com/.*?)"', info_page)
        if m_yt is not None:
            self.to_screen(u'Youtube video detected')
            return self.url_result(m_yt.group(1), 'Youtube')
        data_json = self._search_regex(r'var vars = ({.*?});', info_page, 'vars')
        data = json.loads(data_json)

        formats = [{
            'format_id': k,
            'url': v,
            'width': int(k[len('url'):]),
        } for k, v in data.items()
            if k.startswith('url')]
        self._sort_formats(formats)

        return {
            'id': compat_str(data['vid']),
            'formats': formats,
            'title': unescapeHTML(data['md_title']),
            'thumbnail': data.get('jpg'),
            'uploader': data.get('md_author'),
            'duration': data.get('duration')
        }
