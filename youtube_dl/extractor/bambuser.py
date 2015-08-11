from __future__ import unicode_literals

import re
import itertools

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
    compat_str,
)
from ..utils import (
    ExtractorError,
    int_or_none,
    float_or_none,
)


class BambuserIE(InfoExtractor):
    IE_NAME = 'bambuser'
    _VALID_URL = r'https?://bambuser\.com/v/(?P<id>\d+)'
    _API_KEY = '005f64509e19a868399060af746a00aa'
    _LOGIN_URL = 'https://bambuser.com/user'
    _NETRC_MACHINE = 'bambuser'

    _TEST = {
        'url': 'http://bambuser.com/v/4050584',
        # MD5 seems to be flaky, see https://travis-ci.org/rg3/youtube-dl/jobs/14051016#L388
        # 'md5': 'fba8f7693e48fd4e8641b3fd5539a641',
        'info_dict': {
            'id': '4050584',
            'ext': 'flv',
            'title': 'Education engineering days - lightning talks',
            'duration': 3741,
            'uploader': 'pixelversity',
            'uploader_id': '344706',
            'timestamp': 1382976692,
            'upload_date': '20131028',
            'view_count': int,
        },
        'params': {
            # It doesn't respect the 'Range' header, it would download the whole video
            # caused the travis builds to fail: https://travis-ci.org/rg3/youtube-dl/jobs/14493845#L59
            'skip_download': True,
        },
    }

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'form_id': 'user_login',
            'op': 'Log in',
            'name': username,
            'pass': password,
        }

        request = compat_urllib_request.Request(
            self._LOGIN_URL, compat_urllib_parse.urlencode(login_form).encode('utf-8'))
        request.add_header('Referer', self._LOGIN_URL)
        response = self._download_webpage(
            request, None, 'Logging in as %s' % username)

        login_error = self._html_search_regex(
            r'(?s)<div class="messages error">(.+?)</div>',
            response, 'login error', default=None)
        if login_error:
            raise ExtractorError(
                'Unable to login: %s' % login_error, expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        video_id = self._match_id(url)

        info = self._download_json(
            'http://player-c.api.bambuser.com/getVideo.json?api_key=%s&vid=%s'
            % (self._API_KEY, video_id), video_id)

        error = info.get('error')
        if error:
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, error), expected=True)

        result = info['result']

        return {
            'id': video_id,
            'title': result['title'],
            'url': result['url'],
            'thumbnail': result.get('preview'),
            'duration': int_or_none(result.get('length')),
            'uploader': result.get('username'),
            'uploader_id': compat_str(result.get('owner', {}).get('uid')),
            'timestamp': int_or_none(result.get('created')),
            'fps': float_or_none(result.get('framerate')),
            'view_count': int_or_none(result.get('views_total')),
            'comment_count': int_or_none(result.get('comment_count')),
        }


class BambuserChannelIE(InfoExtractor):
    IE_NAME = 'bambuser:channel'
    _VALID_URL = r'https?://bambuser\.com/channel/(?P<user>.*?)(?:/|#|\?|$)'
    # The maximum number we can get with each request
    _STEP = 50
    _TEST = {
        'url': 'http://bambuser.com/channel/pixelversity',
        'info_dict': {
            'title': 'pixelversity',
        },
        'playlist_mincount': 60,
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        user = mobj.group('user')
        urls = []
        last_id = ''
        for i in itertools.count(1):
            req_url = (
                'http://bambuser.com/xhr-api/index.php?username={user}'
                '&sort=created&access_mode=0%2C1%2C2&limit={count}'
                '&method=broadcast&format=json&vid_older_than={last}'
            ).format(user=user, count=self._STEP, last=last_id)
            req = compat_urllib_request.Request(req_url)
            # Without setting this header, we wouldn't get any result
            req.add_header('Referer', 'http://bambuser.com/channel/%s' % user)
            data = self._download_json(
                req, user, 'Downloading page %d' % i)
            results = data['result']
            if not results:
                break
            last_id = results[-1]['vid']
            urls.extend(self.url_result(v['page'], 'Bambuser') for v in results)

        return {
            '_type': 'playlist',
            'title': user,
            'entries': urls,
        }
