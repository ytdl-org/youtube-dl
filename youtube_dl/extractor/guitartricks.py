# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .wistia import WistiaIE
from ..compat import (
    compat_str,
    compat_kwargs,
)
from ..utils import (
    clean_html,
    ExtractorError,
    get_element_by_class,
    urlencode_postdata,
    urljoin,
)

class GuitarTricksIE(InfoExtractor):
    IE_NAME = 'guitartricks'
    _LOGIN_URL = 'https://www.guitartricks.com/login.php'
    _ORIGIN_URL = 'https://www.guitartricks.com'
    _NETRC_MACHINE = 'guitartricks'
    _VALID_URL = r'https?://(?:www\.)?guitartricks\.com/(lesson|course|tutorial).php\?input=(?P<id>[A-Za-z0-9]+.*)'

    _TESTS = [{
        'url': 'https://www.guitartricks.com/lesson.php?input=21986',
        'md5': '09e89ad6c6a9b85b0471b80230995fcc',
        'info_dict': {
            'id': '5706o2esuo',
            'ext': 'mp4',
            'title': 'Guitar Lessons: Common Models of Guitars',
            'description': 'Let\'s take a look at the most common models of guitars, and learn a bit about what they have in common, as well as what sets them apart from each other. If you have a guitar already, this will help you understand your instrument a little better, and make sure it is the best model for you. If you are still looking for the right model of guitar for you, this should help you make that important decision.\r\n',
            'upload_date': '20160718',
            'timestamp': 1468852802,
        },
    }, {
        'url': 'https://www.guitartricks.com/lesson.php?input=21987',
        'md5': '41f156090b82630c17b866f9ea9df854',
        'info_dict': {
            'id': 'nmxkzhog3w',
            'ext': 'mp4',
            'title': 'Guitar Lessons: How to Hold the Acoustic Guitar',
            'description': 'Holding the acoustic guitar properly is super-important to establishing proper angles for your body, arms, and hands. Every little thing can make a difference, from the height and design of your chair, to the length of your guitar strap. Make sure you are holding your acoustic guitar in such a way as to maximize your ability to learn really good playing habits and technique.',
            'upload_date': '20160718',
            'timestamp': 1468852808,
        }
    }, {
        'url': 'https://www.guitartricks.com/lesson.php?input=24742',
        'md5': '09e89ad6c6a9b85b0471b80230995fcc',
        'info_dict': {
            'id': '5706o2esuo',
            'ext': 'mp4',
        },
    }]


    def _download_webpage(self, *args, **kwargs):
        kwargs.setdefault('headers', {})['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 (KHTML, like Gecko) Version/10.1.1 Safari/603.2.4'
        return super(GuitarTricksIE, self)._download_webpage(
            *args, **compat_kwargs(kwargs))

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        return

        login_popup = self._download_webpage(
            self._LOGIN_URL, None, 'Downloading login popup')

        def is_logged(webpage):
            return any(re.search(p, webpage) for p in (
                r'<a[^>]+\bhref=["\']/logout.php',
                r'>Logout<'))

        # already logged in
        if is_logged(login_popup):
            return


        login_form = self._form_hidden_inputs(login_popup)

        login_form.update({
            'vb_login_username': username,
            'vb_login_password': password,
        })


        response = self._download_webpage(
            self._LOGIN_URL, None, 'Logging in',
            data=urlencode_postdata(login_form),
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': self._ORIGIN_URL,
                'Origin': self._ORIGIN_URL,
            })


        if not is_logged(response):
            error = self._html_search_regex(
                r'(?s)<div[^>]+class="form-errors[^"]*">(.+?)</div>',
                response, 'error message', default=None)
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')
        

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)


        if re.search(r'Full Access Members Only', webpage):
            self.raise_login_required('Full Access Members Only')

        wistia_url = WistiaIE._extract_url(webpage)
        if not wistia_url:
            if any(re.search(p, webpage) for p in (
                    r'Full Access Members Only')):
                self.raise_login_required('Lecture contents locked')

        title = self._og_search_title(webpage, default=None)

        return {
            'id': video_id,
            '_type': 'url_transparent',
            'url': wistia_url,
            'ie_key': WistiaIE.ie_key(),
            'title': title,
            'description': self._og_search_description(webpage),
            # TODO more properties (see youtube_dl/extractor/common.py)
        }