from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    HEADRequest,
    sanitized_Request,
    urlencode_postdata,
)


class GDCVaultIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?gdcvault\.com/play/(?P<id>\d+)/(?P<name>(\w|-)+)?'
    _NETRC_MACHINE = 'gdcvault'
    _TESTS = [
        {
            'url': 'http://www.gdcvault.com/play/1019721/Doki-Doki-Universe-Sweet-Simple',
            'md5': '7ce8388f544c88b7ac11c7ab1b593704',
            'info_dict': {
                'id': '1019721',
                'display_id': 'Doki-Doki-Universe-Sweet-Simple',
                'ext': 'mp4',
                'title': 'Doki-Doki Universe: Sweet, Simple and Genuine (GDC Next 10)'
            }
        },
        {
            'url': 'http://www.gdcvault.com/play/1015683/Embracing-the-Dark-Art-of',
            'info_dict': {
                'id': '1015683',
                'display_id': 'Embracing-the-Dark-Art-of',
                'ext': 'flv',
                'title': 'Embracing the Dark Art of Mathematical Modeling in AI'
            },
            'params': {
                'skip_download': True,  # Requires rtmpdump
            }
        },
        {
            'url': 'http://www.gdcvault.com/play/1015301/Thexder-Meets-Windows-95-or',
            'md5': 'a5eb77996ef82118afbbe8e48731b98e',
            'info_dict': {
                'id': '1015301',
                'display_id': 'Thexder-Meets-Windows-95-or',
                'ext': 'flv',
                'title': 'Thexder Meets Windows 95, or Writing Great Games in the Windows 95 Environment',
            },
            'skip': 'Requires login',
        },
        {
            'url': 'http://gdcvault.com/play/1020791/',
            'only_matching': True,
        },
        {
            # Hard-coded hostname
            'url': 'http://gdcvault.com/play/1023460/Tenacious-Design-and-The-Interface',
            'md5': 'a8efb6c31ed06ca8739294960b2dbabd',
            'info_dict': {
                'id': '1023460',
                'ext': 'mp4',
                'display_id': 'Tenacious-Design-and-The-Interface',
                'title': 'Tenacious Design and The Interface of \'Destiny\'',
            },
        },
        {
            # Multiple audios
            'url': 'http://www.gdcvault.com/play/1014631/Classic-Game-Postmortem-PAC',
            'info_dict': {
                'id': '1014631',
                'ext': 'flv',
                'title': 'How to Create a Good Game - From My Experience of Designing Pac-Man',
            },
            'params': {
                'skip_download': True,  # Requires rtmpdump
                'format': 'jp',  # The japanese audio
            }
        },
        {
            # gdc-player.html
            'url': 'http://www.gdcvault.com/play/1435/An-American-engine-in-Tokyo',
            'info_dict': {
                'id': '1435',
                'display_id': 'An-American-engine-in-Tokyo',
                'ext': 'flv',
                'title': 'An American Engine in Tokyo:/nThe collaboration of Epic Games and Square Enix/nFor THE LAST REMINANT',
            },
            'params': {
                'skip_download': True,  # Requires rtmpdump
            },
        },
    ]

    def _login(self, webpage_url, display_id):
        username, password = self._get_login_info()
        if username is None or password is None:
            self.report_warning('It looks like ' + webpage_url + ' requires a login. Try specifying a username and password and try again.')
            return None

        mobj = re.match(r'(?P<root_url>https?://.*?/).*', webpage_url)
        login_url = mobj.group('root_url') + 'api/login.php'
        logout_url = mobj.group('root_url') + 'logout'

        login_form = {
            'email': username,
            'password': password,
        }

        request = sanitized_Request(login_url, urlencode_postdata(login_form))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        self._download_webpage(request, display_id, 'Logging in')
        start_page = self._download_webpage(webpage_url, display_id, 'Getting authenticated video page')
        self._download_webpage(logout_url, display_id, 'Logging out')

        return start_page

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        video_id = mobj.group('id')
        display_id = mobj.group('name') or video_id

        webpage_url = 'http://www.gdcvault.com/play/' + video_id
        start_page = self._download_webpage(webpage_url, display_id)

        direct_url = self._search_regex(
            r's1\.addVariable\("file",\s*encodeURIComponent\("(/[^"]+)"\)\);',
            start_page, 'url', default=None)
        if direct_url:
            title = self._html_search_regex(
                r'<td><strong>Session Name</strong></td>\s*<td>(.*?)</td>',
                start_page, 'title')
            video_url = 'http://www.gdcvault.com' + direct_url
            # resolve the url so that we can detect the correct extension
            head = self._request_webpage(HEADRequest(video_url), video_id)
            video_url = head.geturl()

            return {
                'id': video_id,
                'display_id': display_id,
                'url': video_url,
                'title': title,
            }

        PLAYER_REGEX = r'<iframe src="(?P<xml_root>.+?)/(?:gdc-)?player.*?\.html.*?".*?</iframe>'

        xml_root = self._html_search_regex(
            PLAYER_REGEX, start_page, 'xml root', default=None)
        if xml_root is None:
            # Probably need to authenticate
            login_res = self._login(webpage_url, display_id)
            if login_res is None:
                self.report_warning('Could not login.')
            else:
                start_page = login_res
                # Grab the url from the authenticated page
                xml_root = self._html_search_regex(
                    PLAYER_REGEX, start_page, 'xml root')

        xml_name = self._html_search_regex(
            r'<iframe src=".*?\?xml=(.+?\.xml).*?".*?</iframe>',
            start_page, 'xml filename', default=None)
        if xml_name is None:
            # Fallback to the older format
            xml_name = self._html_search_regex(
                r'<iframe src=".*?\?xmlURL=xml/(?P<xml_file>.+?\.xml).*?".*?</iframe>',
                start_page, 'xml filename')

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'display_id': display_id,
            'url': '%s/xml/%s' % (xml_root, xml_name),
            'ie_key': 'DigitallySpeaking',
        }
