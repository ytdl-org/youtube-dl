# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from .wistia import WistiaIE
from ..compat import (
    compat_str,
    compat_HTTPError,
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
    _LOGIN_REQUIRED = False

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
        'md5': '98074943181f87361f16085b0370717d',
        'info_dict': {
            'id': '4h7kvsarcg',
            'ext': 'mp4',
            'title': 'Guitar Lessons: The \'Magic L\', in Reverse!',
            'description': "Let's flip the Magic L on it's head and open up a whole new set of options for playing in a variety of keys.\r\n\r\nThe Reverse Magic L is like the \u2018Magic L\u2019 you already learned, only it is turned upside down! \r\n\r\nThe 1 chord is played as a 5th-string power chord, and the IV and the V chords will fall into place as 6th string power chords, in an upside-down L shape. \r\n\r\nListen to how these three chords sound intuitively right together. \r\n",
            'upload_date': '20160718',
            'timestamp': 1468854273,
        },
    }]

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            if self._LOGIN_REQUIRED:
                raise ExtractorError('No login info available, needed for using %s.' % self.IE_NAME, expected=True)
            return

        def fail(message):
            raise ExtractorError(
                'Unable to login. GuitarTricks said: %s' % message, expected=True)

        def login_step(page, urlh, note, data):
            form = self._hidden_inputs(page)
            form.update(data)

            page_url = urlh.geturl()
            post_url = '/process/loginAjax'
            post_url = urljoin(page_url, post_url)        

            headers = {'Referer': page_url}

            try:
                response = self._download_json(
                    post_url, None, note,
                    data=urlencode_postdata(form),
                    headers=headers)
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                    response = self._parse_json(
                        e.cause.read().decode('utf-8'), None)
                    fail(response.get('message') or response['errors'][0])
                raise

            if response.get('status'):
                return None, None
            else:
                fail(response.get('error'))

            redirect_url = 'https://www.guitartricks.com/main.php'
            return self._download_webpage_handle(
                redirect_url, None, 'Downloading login redirect page',
                headers=headers)

        login_page, handle= self._download_webpage_handle(
            self._LOGIN_URL, None, 'Downloading login page')

        redirect_page, handle = login_step(
            login_page, handle, 'Logging in', {
                'login': username,
                'password': password,
                'action': 'verify_login',
            })

        # Successful login
        if not redirect_page:
            return
        
    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        if re.search(r'Full Access Members Only', webpage):
            raise ExtractorError('Video only available with premium plan', expected=True)

        wistia_url = WistiaIE._extract_url(webpage)

        title = self._og_search_title(webpage, default=None)

        return {
            'id': video_id,
            '_type': 'url_transparent',
            'url': wistia_url,
            'ie_key': WistiaIE.ie_key(),
            'title': title,
            'description': self._og_search_description(webpage),
        }