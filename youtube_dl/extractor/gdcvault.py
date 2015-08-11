from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import (
    compat_urllib_parse,
    compat_urllib_request,
)
from ..utils import (
    remove_end,
    HEADRequest,
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
        }
    ]

    def _parse_mp4(self, xml_description):
        video_formats = []
        mp4_video = xml_description.find('./metadata/mp4video')
        if mp4_video is None:
            return None

        mobj = re.match(r'(?P<root>https?://.*?/).*', mp4_video.text)
        video_root = mobj.group('root')
        formats = xml_description.findall('./metadata/MBRVideos/MBRVideo')
        for format in formats:
            mobj = re.match(r'mp4\:(?P<path>.*)', format.find('streamName').text)
            url = video_root + mobj.group('path')
            vbr = format.find('bitrate').text
            video_formats.append({
                'url': url,
                'vbr': int(vbr),
            })
        return video_formats

    def _parse_flv(self, xml_description):
        formats = []
        akamai_url = xml_description.find('./metadata/akamaiHost').text
        audios = xml_description.find('./metadata/audios')
        if audios is not None:
            for audio in audios:
                formats.append({
                    'url': 'rtmp://%s/ondemand?ovpfv=1.1' % akamai_url,
                    'play_path': remove_end(audio.get('url'), '.flv'),
                    'ext': 'flv',
                    'vcodec': 'none',
                    'format_id': audio.get('code'),
                })
        slide_video_path = xml_description.find('./metadata/slideVideo').text
        formats.append({
            'url': 'rtmp://%s/ondemand?ovpfv=1.1' % akamai_url,
            'play_path': remove_end(slide_video_path, '.flv'),
            'ext': 'flv',
            'format_note': 'slide deck video',
            'quality': -2,
            'preference': -2,
            'format_id': 'slides',
        })
        speaker_video_path = xml_description.find('./metadata/speakerVideo').text
        formats.append({
            'url': 'rtmp://%s/ondemand?ovpfv=1.1' % akamai_url,
            'play_path': remove_end(speaker_video_path, '.flv'),
            'ext': 'flv',
            'format_note': 'speaker video',
            'quality': -1,
            'preference': -1,
            'format_id': 'speaker',
        })
        return formats

    def _login(self, webpage_url, display_id):
        (username, password) = self._get_login_info()
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

        request = compat_urllib_request.Request(login_url, compat_urllib_parse.urlencode(login_form))
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

        xml_root = self._html_search_regex(
            r'<iframe src="(?P<xml_root>.*?)player.html.*?".*?</iframe>',
            start_page, 'xml root', default=None)
        if xml_root is None:
            # Probably need to authenticate
            login_res = self._login(webpage_url, display_id)
            if login_res is None:
                self.report_warning('Could not login.')
            else:
                start_page = login_res
                # Grab the url from the authenticated page
                xml_root = self._html_search_regex(
                    r'<iframe src="(.*?)player.html.*?".*?</iframe>',
                    start_page, 'xml root')

        xml_name = self._html_search_regex(
            r'<iframe src=".*?\?xml=(.+?\.xml).*?".*?</iframe>',
            start_page, 'xml filename', default=None)
        if xml_name is None:
            # Fallback to the older format
            xml_name = self._html_search_regex(r'<iframe src=".*?\?xmlURL=xml/(?P<xml_file>.+?\.xml).*?".*?</iframe>', start_page, 'xml filename')

        xml_description_url = xml_root + 'xml/' + xml_name
        xml_description = self._download_xml(xml_description_url, display_id)

        video_title = xml_description.find('./metadata/title').text
        video_formats = self._parse_mp4(xml_description)
        if video_formats is None:
            video_formats = self._parse_flv(xml_description)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': video_title,
            'formats': video_formats,
        }
