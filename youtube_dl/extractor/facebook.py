from __future__ import unicode_literals

import json
import re
import socket

from .common import InfoExtractor
from ..utils import (
    compat_http_client,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_request,
    urlencode_postdata,

    ExtractorError,
)


class FacebookIE(InfoExtractor):
    _VALID_URL = r'''(?x)
        https?://(?:\w+\.)?facebook\.com/
        (?:[^#?]*\#!/)?
        (?:video/video\.php|photo\.php|video/embed)\?(?:.*?)
        (?:v|video_id)=(?P<id>[0-9]+)
        (?:.*)'''
    _LOGIN_URL = 'https://www.facebook.com/login.php?next=http%3A%2F%2Ffacebook.com%2Fhome.php&login_attempt=1'
    _CHECKPOINT_URL = 'https://www.facebook.com/checkpoint/?next=http%3A%2F%2Ffacebook.com%2Fhome.php&_fb_noscript=1'
    _NETRC_MACHINE = 'facebook'
    IE_NAME = 'facebook'
    _TEST = {
        'url': 'https://www.facebook.com/photo.php?v=120708114770723',
        'md5': '48975a41ccc4b7a581abd68651c1a5a8',
        'info_dict': {
            'id': '120708114770723',
            'ext': 'mp4',
            'duration': 279,
            'title': 'PEOPLE ARE AWESOME 2013',
        }
    }

    def _login(self):
        (useremail, password) = self._get_login_info()
        if useremail is None:
            return

        login_page_req = compat_urllib_request.Request(self._LOGIN_URL)
        login_page_req.add_header('Cookie', 'locale=en_US')
        login_page = self._download_webpage(login_page_req, None,
            note='Downloading login page',
            errnote='Unable to download login page')
        lsd = self._search_regex(
            r'<input type="hidden" name="lsd" value="([^"]*)"',
            login_page, 'lsd')
        lgnrnd = self._search_regex(r'name="lgnrnd" value="([^"]*?)"', login_page, 'lgnrnd')

        login_form = {
            'email': useremail,
            'pass': password,
            'lsd': lsd,
            'lgnrnd': lgnrnd,
            'next': 'http://facebook.com/home.php',
            'default_persistent': '0',
            'legacy_return': '1',
            'timezone': '-60',
            'trynum': '1',
            }
        request = compat_urllib_request.Request(self._LOGIN_URL, urlencode_postdata(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            login_results = self._download_webpage(request, None,
                note='Logging in', errnote='unable to fetch login page')
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                self._downloader.report_warning('unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
                return

            check_form = {
                'fb_dtsg': self._search_regex(r'name="fb_dtsg" value="(.+?)"', login_results, 'fb_dtsg'),
                'nh': self._search_regex(r'name="nh" value="(\w*?)"', login_results, 'nh'),
                'name_action_selected': 'dont_save',
                'submit[Continue]': self._search_regex(r'<button[^>]+value="(.*?)"[^>]+name="submit\[Continue\]"', login_results, 'continue'),
            }
            check_req = compat_urllib_request.Request(self._CHECKPOINT_URL, urlencode_postdata(check_form))
            check_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            check_response = self._download_webpage(check_req, None,
                note='Confirming login')
            if re.search(r'id="checkpointSubmitButton"', check_response) is not None:
                self._downloader.report_warning('Unable to confirm login, you have to login in your brower and authorize the login.')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning('unable to log in: %s' % compat_str(err))
            return

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        url = 'https://www.facebook.com/video/video.php?v=%s' % video_id
        webpage = self._download_webpage(url, video_id)

        BEFORE = '{swf.addParam(param[0], param[1]);});\n'
        AFTER = '.forEach(function(variable) {swf.addVariable(variable[0], variable[1]);});'
        m = re.search(re.escape(BEFORE) + '(.*?)' + re.escape(AFTER), webpage)
        if not m:
            m_msg = re.search(r'class="[^"]*uiInterstitialContent[^"]*"><div>(.*?)</div>', webpage)
            if m_msg is not None:
                raise ExtractorError(
                    'The video is not available, Facebook said: "%s"' % m_msg.group(1),
                    expected=True)
            else:
                raise ExtractorError('Cannot parse data')
        data = dict(json.loads(m.group(1)))
        params_raw = compat_urllib_parse.unquote(data['params'])
        params = json.loads(params_raw)
        video_data = params['video_data'][0]
        video_url = video_data.get('hd_src')
        if not video_url:
            video_url = video_data['sd_src']
        if not video_url:
            raise ExtractorError('Cannot find video URL')

        video_title = self._html_search_regex(
            r'<h2 class="uiHeaderTitle">([^<]*)</h2>', webpage, 'title')

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'duration': int(video_data['video_duration']),
            'thumbnail': video_data['thumbnail_src'],
        }
