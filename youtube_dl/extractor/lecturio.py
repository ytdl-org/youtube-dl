# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..compat import compat_str
from ..utils import (
    determine_ext,
    extract_attributes,
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    url_or_none,
    urlencode_postdata,
    urljoin,
)


class LecturioBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://app.lecturio.com/en/login'
    _NETRC_MACHINE = 'lecturio'

    def _real_initialize(self):
        self._login()

    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        # Sets some cookies
        _, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Downloading login popup')

        def is_logged(url_handle):
            return self._LOGIN_URL not in compat_str(url_handle.geturl())

        # Already logged in
        if is_logged(urlh):
            return

        login_form = {
            'signin[email]': username,
            'signin[password]': password,
            'signin[remember]': 'on',
        }

        response, urlh = self._download_webpage_handle(
            self._LOGIN_URL, None, 'Logging in',
            data=urlencode_postdata(login_form))

        # Logged in successfully
        if is_logged(urlh):
            return

        errors = self._html_search_regex(
            r'(?s)<ul[^>]+class=["\']error_list[^>]+>(.+?)</ul>', response,
            'errors', default=None)
        if errors:
            raise ExtractorError('Unable to login: %s' % errors, expected=True)
        raise ExtractorError('Unable to log in')


class LecturioIE(LecturioBaseIE):
    _VALID_URL = r'''(?x)
                    https://
                        (?:
                            app\.lecturio\.com/[^/]+/(?P<id>[^/?#&]+)\.lecture|
                            (?:www\.)?lecturio\.de/[^/]+/(?P<id_de>[^/?#&]+)\.vortrag
                        )
                    '''
    _TESTS = [{
        'url': 'https://app.lecturio.com/medical-courses/important-concepts-and-terms-introduction-to-microbiology.lecture#tab/videos',
        'md5': 'f576a797a5b7a5e4e4bbdfc25a6a6870',
        'info_dict': {
            'id': '39634',
            'ext': 'mp4',
            'title': 'Important Concepts and Terms – Introduction to Microbiology',
        },
        'skip': 'Requires lecturio account credentials',
    }, {
        'url': 'https://www.lecturio.de/jura/oeffentliches-recht-staatsexamen.vortrag',
        'only_matching': True,
    }]

    _CC_LANGS = {
        'German': 'de',
        'English': 'en',
        'Spanish': 'es',
        'French': 'fr',
        'Polish': 'pl',
        'Russian': 'ru',
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id') or mobj.group('id_de')

        webpage = self._download_webpage(
            'https://app.lecturio.com/en/lecture/%s/player.html' % display_id,
            display_id)

        lecture_id = self._search_regex(
            r'lecture_id\s*=\s*(?:L_)?(\d+)', webpage, 'lecture id')

        api_url = self._search_regex(
            r'lectureDataLink\s*:\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
            'api url', group='url')

        video = self._download_json(api_url, display_id)

        title = video['title'].strip()

        formats = []
        for format_ in video['content']['media']:
            if not isinstance(format_, dict):
                continue
            file_ = format_.get('file')
            if not file_:
                continue
            ext = determine_ext(file_)
            if ext == 'smil':
                # smil contains only broken RTMP formats anyway
                continue
            file_url = url_or_none(file_)
            if not file_url:
                continue
            label = str_or_none(format_.get('label'))
            filesize = int_or_none(format_.get('fileSize'))
            formats.append({
                'url': file_url,
                'format_id': label,
                'filesize': float_or_none(filesize, invscale=1000)
            })
        self._sort_formats(formats)

        subtitles = {}
        automatic_captions = {}
        cc = self._parse_json(
            self._search_regex(
                r'subtitleUrls\s*:\s*({.+?})\s*,', webpage, 'subtitles',
                default='{}'), display_id, fatal=False)
        for cc_label, cc_url in cc.items():
            cc_url = url_or_none(cc_url)
            if not cc_url:
                continue
            lang = self._search_regex(
                r'/([a-z]{2})_', cc_url, 'lang',
                default=cc_label.split()[0] if cc_label else 'en')
            original_lang = self._search_regex(
                r'/[a-z]{2}_([a-z]{2})_', cc_url, 'original lang',
                default=None)
            sub_dict = (automatic_captions
                        if 'auto-translated' in cc_label or original_lang
                        else subtitles)
            sub_dict.setdefault(self._CC_LANGS.get(lang, lang), []).append({
                'url': cc_url,
            })

        return {
            'id': lecture_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'automatic_captions': automatic_captions,
        }


class LecturioCourseIE(LecturioBaseIE):
    _VALID_URL = r'https://app\.lecturio\.com/[^/]+/(?P<id>[^/?#&]+)\.course'
    _TEST = {
        'url': 'https://app.lecturio.com/medical-courses/microbiology-introduction.course#/',
        'info_dict': {
            'id': 'microbiology-introduction',
            'title': 'Microbiology: Introduction',
        },
        'playlist_count': 45,
        'skip': 'Requires lecturio account credentials',
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        entries = []
        for mobj in re.finditer(
                r'(?s)<[^>]+\bdata-url=(["\'])(?:(?!\1).)+\.lecture\b[^>]+>',
                webpage):
            params = extract_attributes(mobj.group(0))
            lecture_url = urljoin(url, params.get('data-url'))
            lecture_id = params.get('data-id')
            entries.append(self.url_result(
                lecture_url, ie=LecturioIE.ie_key(), video_id=lecture_id))

        title = self._search_regex(
            r'<span[^>]+class=["\']content-title[^>]+>([^<]+)', webpage,
            'title', default=None)

        return self.playlist_result(entries, display_id, title)


class LecturioDeCourseIE(LecturioBaseIE):
    _VALID_URL = r'https://(?:www\.)?lecturio\.de/[^/]+/(?P<id>[^/?#&]+)\.kurs'
    _TEST = {
        'url': 'https://www.lecturio.de/jura/grundrechte.kurs',
        'only_matching': True,
    }

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        entries = []
        for mobj in re.finditer(
                r'(?s)<td[^>]+\bdata-lecture-id=["\'](?P<id>\d+).+?\bhref=(["\'])(?P<url>(?:(?!\2).)+\.vortrag)\b[^>]+>',
                webpage):
            lecture_url = urljoin(url, mobj.group('url'))
            lecture_id = mobj.group('id')
            entries.append(self.url_result(
                lecture_url, ie=LecturioIE.ie_key(), video_id=lecture_id))

        title = self._search_regex(
            r'<h1[^>]*>([^<]+)', webpage, 'title', default=None)

        return self.playlist_result(entries, display_id, title)
