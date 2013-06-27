import json
import netrc
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
    _LOGIN_URL = 'https://login.facebook.com/login.php?m&next=http%3A%2F%2Fm.facebook.com%2Fhome.php&'
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

    def _real_initialize(self):
        if self._downloader is None:
            return

        useremail = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username', None) is not None:
            useremail = downloader_params['username']
            password = downloader_params['password']
        elif downloader_params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(self._NETRC_MACHINE)
                if info is not None:
                    useremail = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(u'parsing .netrc: %s' % compat_str(err))
                return

        if useremail is None:
            return

        # Log in
        login_form = {
            'email': useremail,
            'pass': password,
            'login': 'Log+In'
            }
        request = compat_urllib_request.Request(self._LOGIN_URL, compat_urllib_parse.urlencode(login_form))
        try:
            self.report_login()
            login_results = compat_urllib_request.urlopen(request).read()
            if re.search(r'<form(.*)name="login"(.*)</form>', login_results) is not None:
                self._downloader.report_warning(u'unable to log in: bad username/password, or exceded login rate limit (~3/min). Check credentials or wait.')
                return
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            self._downloader.report_warning(u'unable to log in: %s' % compat_str(err))
            return

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

        video_title = self._html_search_regex('<h2 class="uiHeaderTitle">([^<]+)</h2>',
            webpage, u'title')

        info = {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'ext': 'mp4',
            'duration': video_duration,
            'thumbnail': thumbnail,
        }
        return [info]
