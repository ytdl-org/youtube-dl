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

    ExtractorError,
)


class FacebookIE(InfoExtractor):
    """Information Extractor for Facebook"""

    _VALID_URL = r'^(?:https?://)?(?:\w+\.)?facebook\.com/(?:video/video|photo)\.php\?(?:.*?)v=(?P<ID>\d+)(?:.*)'
    _LOGIN_URL = 'https://www.facebook.com/login.php?next=http%3A%2F%2Ffacebook.com%2Fhome.php&login_attempt=1'
    _CHECKPOINT_URL = 'https://www.facebook.com/checkpoint/?next=http%3A%2F%2Ffacebook.com%2Fhome.php&_fb_noscript=1'
    _NETRC_MACHINE = 'facebook'
    IE_NAME = u'facebook'
    _TEST = {
        u'url': u'https://www.facebook.com/photo.php?v=120708114770723',
        u'file': u'120708114770723.mp4',
        u'md5': u'48975a41ccc4b7a581abd68651c1a5a8',
        u'info_dict': {
            u"duration": 279, 
            u"title": u"PEOPLE ARE AWESOME 2013"
        }
    }

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen(u'Logging in')

    def _login(self):
        (useremail, password) = self._get_login_info()
        if useremail is None:
            return

        login_page_req = compat_urllib_request.Request(self._LOGIN_URL)
        login_page_req.add_header('Cookie', 'locale=en_US')
        self.report_login()
        login_page = self._download_webpage(login_page_req, None, note=False,
            errnote=u'Unable to download login page')
        lsd = self._search_regex(r'"lsd":"(\w*?)"', login_page, u'lsd')
        lgnrnd = self._search_regex(r'name="lgnrnd" value="([^"]*?)"', login_page, u'lgnrnd')

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
        request = compat_urllib_request.Request(self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            login_results = compat_urllib_request.urlopen(request).read()
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
                return

            check_form = {
                'fb_dtsg': self._search_regex(r'"fb_dtsg":"(.*?)"', login_results, u'fb_dtsg'),
                'nh': self._search_regex(r'name="nh" value="(\w*?)"', login_results, u'nh'),
                'name_action_selected': 'dont_save',
                'submit[Continue]': self._search_regex(r'<input value="(.*?)" name="submit\[Continue\]"', login_results, u'continue'),
            }
            check_req = compat_urllib_request.Request(self._CHECKPOINT_URL, compat_urllib_parse.urlencode(check_form))
            check_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            check_response = compat_urllib_request.urlopen(check_req).read()
            if re.search(r'id="checkpointSubmitButton"', check_response) is not None:
                self._downloader.report_warning(u'Unable to confirm login, you have to login in your brower and authorize the login.')
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError(u'Invalid URL: %s' % url)
        video_id = mobj.group('ID')

        url = 'https://www.facebook.com/video/video.php?v=%s' % video_id
        webpage = self._download_webpage(url, video_id)

        BEFORE = '{swf.addParam(param[0], param[1]);});\n'
        AFTER = '.forEach(function(variable) {swf.addVariable(variable[0], variable[1]);});'
        m = re.search(re.escape(BEFORE) + '(.*?)' + re.escape(AFTER), webpage)
        if not m:
            m_msg = re.search(r'class="[^"]*uiInterstitialContent[^"]*"><div>(.*?)</div>', webpage)
            if m_msg is not None:
                raise ExtractorError(
                    u'The video is not available, Facebook said: "%s"' % m_msg.group(1),
                    expected=True)
            else:
                raise ExtractorError(u'Cannot parse data')
        data = dict(json.loads(m.group(1)))
        params_raw = compat_urllib_parse.unquote(data['params'])
        params = json.loads(params_raw)
        video_data = params['video_data'][0]
        video_url = video_data.get('hd_src')
        if not video_url:
            video_url = video_data['sd_src']
        if not video_url:
            raise ExtractorError(u'Cannot find video URL')
        video_duration = int(video_data['video_duration'])
        thumbnail = video_data['thumbnail_src']

        video_title = self._html_search_regex(
            r'<h2 class="uiHeaderTitle">([^<]*)</h2>', webpage, u'title')

        info = {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': 'mp4',
            'duration': video_duration,
            'thumbnail': thumbnail,
        }
        return [info]
