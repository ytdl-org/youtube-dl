# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    strip_or_none,
    unescapeHTML,
    urlencode_postdata,
)


class RoosterTeethIE(InfoExtractor):
    _VALID_URL = r'https?://(?:.+?\.)?roosterteeth\.com/episode/(?P<id>[^/?#&]+)'
    _LOGIN_URL = 'https://roosterteeth.com/login'
    _NETRC_MACHINE = 'roosterteeth'
    _TESTS = [{
        'url': 'http://roosterteeth.com/episode/million-dollars-but-season-2-million-dollars-but-the-game-announcement',
        'md5': 'e2bd7764732d785ef797700a2489f212',
        'info_dict': {
            'id': '26576',
            'display_id': 'million-dollars-but-season-2-million-dollars-but-the-game-announcement',
            'ext': 'mp4',
            'title': 'Million Dollars, But...: Million Dollars, But... The Game Announcement',
            'description': 'md5:0cc3b21986d54ed815f5faeccd9a9ca5',
            'thumbnail': 're:^https?://.*\.png$',
            'series': 'Million Dollars, But...',
            'episode': 'Million Dollars, But... The Game Announcement',
            'comment_count': int,
        },
    }, {
        'url': 'http://achievementhunter.roosterteeth.com/episode/off-topic-the-achievement-hunter-podcast-2016-i-didn-t-think-it-would-pass-31',
        'only_matching': True,
    }, {
        'url': 'http://funhaus.roosterteeth.com/episode/funhaus-shorts-2016-austin-sucks-funhaus-shorts',
        'only_matching': True,
    }, {
        'url': 'http://screwattack.roosterteeth.com/episode/death-battle-season-3-mewtwo-vs-shadow',
        'only_matching': True,
    }, {
        'url': 'http://theknow.roosterteeth.com/episode/the-know-game-news-season-1-boring-steam-sales-are-better',
        'only_matching': True,
    }, {
        # only available for FIRST members
        'url': 'http://roosterteeth.com/episode/rt-docs-the-world-s-greatest-head-massage-the-world-s-greatest-head-massage-an-asmr-journey-part-one',
        'only_matching': True,
    }]

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_page = self._download_webpage(
            self._LOGIN_URL, None,
            note='Downloading login page',
            errnote='Unable to download login page')

        login_form = self._hidden_inputs(login_page)

        login_form.update({
            'username': username,
            'password': password,
        })

        login_request = self._download_webpage(
            self._LOGIN_URL, None,
            note='Logging in as %s' % username,
            data=urlencode_postdata(login_form),
            headers={
                'Referer': self._LOGIN_URL,
            })

        if not any(re.search(p, login_request) for p in (
                r'href=["\']https?://(?:www\.)?roosterteeth\.com/logout"',
                r'>Sign Out<')):
            error = self._html_search_regex(
                r'(?s)<div[^>]+class=(["\']).*?\balert-danger\b.*?\1[^>]*>(?:\s*<button[^>]*>.*?</button>)?(?P<error>.+?)</div>',
                login_request, 'alert', default=None, group='error')
            if error:
                raise ExtractorError('Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        episode = strip_or_none(unescapeHTML(self._search_regex(
            (r'videoTitle\s*=\s*(["\'])(?P<title>(?:(?!\1).)+)\1',
             r'<title>(?P<title>[^<]+)</title>'), webpage, 'title',
            default=None, group='title')))

        title = strip_or_none(self._og_search_title(
            webpage, default=None)) or episode

        m3u8_url = self._search_regex(
            r'file\s*:\s*(["\'])(?P<url>http.+?\.m3u8.*?)\1',
            webpage, 'm3u8 url', default=None, group='url')

        if not m3u8_url:
            if re.search(r'<div[^>]+class=["\']non-sponsor', webpage):
                self.raise_login_required(
                    '%s is only available for FIRST members' % display_id)

            if re.search(r'<div[^>]+class=["\']golive-gate', webpage):
                self.raise_login_required('%s is not available yet' % display_id)

            raise ExtractorError('Unable to extract m3u8 URL')

        formats = self._extract_m3u8_formats(
            m3u8_url, display_id, ext='mp4',
            entry_protocol='m3u8_native', m3u8_id='hls')
        self._sort_formats(formats)

        description = strip_or_none(self._og_search_description(webpage))
        thumbnail = self._proto_relative_url(self._og_search_thumbnail(webpage))

        series = self._search_regex(
            (r'<h2>More ([^<]+)</h2>', r'<a[^>]+>See All ([^<]+) Videos<'),
            webpage, 'series', fatal=False)

        comment_count = int_or_none(self._search_regex(
            r'>Comments \((\d+)\)<', webpage,
            'comment count', fatal=False))

        video_id = self._search_regex(
            (r'containerId\s*=\s*["\']episode-(\d+)\1',
             r'<div[^<]+id=["\']episode-(\d+)'), webpage,
            'video id', default=display_id)

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'series': series,
            'episode': episode,
            'comment_count': comment_count,
            'formats': formats,
        }
