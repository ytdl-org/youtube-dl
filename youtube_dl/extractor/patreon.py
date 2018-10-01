# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import js_to_json


class PatreonIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?patreon\.com/creation\?hid=(?P<id>[^&#]+)'
    _TESTS = [
        {
            'url': 'http://www.patreon.com/creation?hid=743933',
            'md5': 'e25505eec1053a6e6813b8ed369875cc',
            'info_dict': {
                'id': '743933',
                'ext': 'mp3',
                'title': 'Episode 166: David Smalley of Dogma Debate',
                'uploader': 'Cognitive Dissonance Podcast',
                'thumbnail': 're:^https?://.*$',
            },
        },
        {
            'url': 'http://www.patreon.com/creation?hid=754133',
            'md5': '3eb09345bf44bf60451b8b0b81759d0a',
            'info_dict': {
                'id': '754133',
                'ext': 'mp3',
                'title': 'CD 167 Extra',
                'uploader': 'Cognitive Dissonance Podcast',
                'thumbnail': 're:^https?://.*$',
            },
        },
        {
            'url': 'https://www.patreon.com/creation?hid=1682498',
            'info_dict': {
                'id': 'SU4fj_aEMVw',
                'ext': 'mp4',
                'title': 'I\'m on Patreon!',
                'uploader': 'TraciJHines',
                'thumbnail': 're:^https?://.*$',
                'upload_date': '20150211',
                'description': 'md5:c5a706b1f687817a3de09db1eb93acd4',
                'uploader_id': 'TraciJHines',
            },
            'params': {
                'noplaylist': True,
                'skip_download': True,
            }
        }
    ]

    # Currently Patreon exposes download URL via hidden CSS, so login is not
    # needed. Keeping this commented for when this inevitably changes.
    '''
    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        login_form = {
            'redirectUrl': 'http://www.patreon.com/',
            'email': username,
            'password': password,
        }

        request = sanitized_Request(
            'https://www.patreon.com/processLogin',
            compat_urllib_parse_urlencode(login_form).encode('utf-8')
        )
        login_page = self._download_webpage(request, None, note='Logging in')

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError('Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()
    '''

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        title = self._og_search_title(webpage).strip()

        attach_fn = self._html_search_regex(
            r'<div class="attach"><a target="_blank" href="([^"]+)">',
            webpage, 'attachment URL', default=None)
        embed = self._html_search_regex(
            r'<div[^>]+id="watchCreation"[^>]*>\s*<iframe[^>]+src="([^"]+)"',
            webpage, 'embedded URL', default=None)

        if attach_fn is not None:
            video_url = 'http://www.patreon.com' + attach_fn
            thumbnail = self._og_search_thumbnail(webpage)
            uploader = self._html_search_regex(
                r'<strong>(.*?)</strong> is creating', webpage, 'uploader')
        elif embed is not None:
            return self.url_result(embed)
        else:
            playlist = self._parse_json(self._search_regex(
                r'(?s)new\s+jPlayerPlaylist\(\s*\{\s*[^}]*},\s*(\[.*?,?\s*\])',
                webpage, 'playlist JSON'),
                video_id, transform_source=js_to_json)
            data = playlist[0]
            video_url = self._proto_relative_url(data['mp3'])
            thumbnail = self._proto_relative_url(data.get('cover'))
            uploader = data.get('artist')

        return {
            'id': video_id,
            'url': video_url,
            'ext': 'mp3',
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
        }
