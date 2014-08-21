# encoding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    compat_html_parser,
    #compat_urllib_request,
    #compat_urllib_parse,
)


class PatreonHTMLParser(compat_html_parser.HTMLParser):
    _PREFIX = 'http://www.patreon.com'
    _ATTACH_TAGS = 5 * ['div']
    _ATTACH_CLASSES = [
        'fancyboxhidden', 'box photo', 'boxwrapper',
        'hiddendisplay shareinfo', 'attach'
    ]
    _INFO_TAGS = 4 * ['div']
    _INFO_CLASSES = [
        'fancyboxhidden', 'box photo', 'boxwrapper',
        'hiddendisplay shareinfo'
    ]

    def _match(self, attrs_classes, desired):
        if attrs_classes == desired:
            return True
        elif len(attrs_classes) == len(desired):
            return all(
                x.startswith(y)
                for x, y in zip(attrs_classes, desired)
            )
        return False

    def get_creation_info(self, html_data):
        self.tag_stack = []
        self.attrs_stack = []
        self.creation_info = {}
        self.feed(html_data)

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag.lower())
        self.attrs_stack.append(dict(attrs))

    def handle_endtag(self, tag):
        self.tag_stack.pop()
        self.attrs_stack.pop()

    def handle_data(self, data):
        # Check first if this is a creation attachment
        if self.tag_stack[-6:-1] == self._ATTACH_TAGS:
            attrs_classes = [
                x.get('class', '').lower() for x in self.attrs_stack[-6:-1]
            ]
            if self._match(attrs_classes, self._ATTACH_CLASSES):
                if self.tag_stack[-1] == 'a':
                    url = self._PREFIX + self.attrs_stack[-1].get('href')
                    self.creation_info['url'] = url
                    if '.' in data:
                        self.creation_info['ext'] = data.rsplit('.')[-1]
        # Next, check if this is within the div containing the creation info
        if self.tag_stack[-5:-1] == self._INFO_TAGS:
            attrs_classes = [
                x.get('class', '').lower() for x in self.attrs_stack[-5:-1]
            ]
            if self._match(attrs_classes, self._INFO_CLASSES):
                if self.attrs_stack[-1].get('class') == 'utitle':
                    self.creation_info['title'] = data.strip()


class PatreonIE(InfoExtractor):
    IE_NAME = 'patreon'
    _VALID_URL = r'https?://(?:www\.)?patreon\.com/creation\?hid=(.+)'
    _TESTS = [
        # CSS names with "double" in the name, i.e. "boxwrapper double"
        {
            'url': 'http://www.patreon.com/creation?hid=743933',
            'md5': 'e25505eec1053a6e6813b8ed369875cc',
            'info_dict': {
                'id': '743933',
                'ext': 'mp3',
                'title': 'Episode 166: David Smalley of Dogma Debate',
                'uploader': 'Cognitive Dissonance Podcast',
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
            },
        },
    ]

    # Currently Patreon exposes download URL via hidden CSS, so login is not
    # needed. Keeping this commented for when this inevitably changes.
    '''
    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_form = {
            'redirectUrl': 'http://www.patreon.com/',
            'email': username,
            'password': password,
        }

        request = compat_urllib_request.Request(
            'https://www.patreon.com/processLogin',
            compat_urllib_parse.urlencode(login_form).encode('utf-8')
        )
        login_page = self._download_webpage(request, None, note='Logging in as %s' % username)

        if re.search(r'onLoginFailed', login_page):
            raise ExtractorError('Unable to login, incorrect username and/or password', expected=True)

    def _real_initialize(self):
        self._login()
    '''

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group(1)

        info_page = self._download_webpage(url, video_id)

        ret = {'id': video_id}
        try:
            ret['uploader'] = re.search(
                r'<strong>(.+)</strong> is creating', info_page
            ).group(1)
        except AttributeError:
            pass

        parser = PatreonHTMLParser()
        parser.get_creation_info(info_page)
        if not parser.creation_info.get('url'):
            raise ExtractorError('Unable to retrieve creation URL')
        ret.update(parser.creation_info)
        return ret
