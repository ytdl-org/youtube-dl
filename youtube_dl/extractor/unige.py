# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
)

from youtube_dl.compat import (
    compat_HTTPError,
)


class UnigeIE(InfoExtractor):
    _VALID_URL = r'https://mediaserver.unige.ch/play/(?P<id>\d+)'
    _TESTS = [{
        'url': 'https://mediaserver.unige.ch/play/196613',
        'md5': 'xxxx',
        'info_dict': {
            'id': '196613',
            'display_id': '196613',
            'ext': 'mp4',
        },
    }, {
        'url': 'https://mediaserver.unige.ch/proxy/196613/VN3-2569-2023-2024-09-19.mp4',
        'only_matching': True,
    }]

    def _login(self, video_id):
        # Login credentials are per video group

        username, password = self._get_login_info(netrc_machine=f'unige-mediaserver-{video_id}')
        if not username or not password:
            self.raise_login_required('You need a username/pwd to access this video')

        try:
            secure_wp = f'https://mediaserver.unige.ch/proxy/{video_id}/secure.php?view=play&id={video_id}'
            self._download_webpage(
                secure_wp, None, 'Logging in',
                data=urlencode_postdata({
                    'httpd_username': username,
                    'httpd_password': password,
                }), headers={
                    'Referer': secure_wp,
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                })
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 400:
                raise ExtractorError(
                    'Unable to login: incorrect username and/or password',
                    expected=True)
            raise

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        try:
            # This dumb download only checks if we need to login, as authentication
            # is unique (and sometimes optional) for each video
            secure_wp = f'https://mediaserver.unige.ch/proxy/{video_id}/secure.php?view=play&id={video_id}'
            self._download_webpage(secure_wp, f'secure_{video_id}')
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                self._login(video_id)
            else:
                # The video doesn't require login
                pass

        video_title = self._html_search_regex(r'<h1>(.+?)</h1>', webpage.replace('\n', ''), 'unige')
        course_title = self._html_search_regex(r'<a href="/collection/[-\w+]+">(?P<course>.*)</a></div>', webpage, 'unige')
        course_id = self._html_search_regex(r'<a href="/collection/(?P<courseid>[-\w+]+)">', webpage, 'unige')

        video_url = self._search_regex(
            r'<source src="([^"]+)"', webpage, 'video URL')

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
            'channel': course_title,
            'channel_id': course_id,
        }


class UnigePlaylistIE(InfoExtractor):
    _VALID_URL = r'https://mediaserver.unige.ch/collection/(?P<id>[-\w+]+)'

    def _real_extract(self, url):
        collection_id = self._match_id(url)

        rss = self._download_xml(url + '.rss', collection_id)

        entries = [self.url_result(video.text, 'Unige')
                   for video in rss.findall('./channel/item/link')]
        title_text = rss.find('./channel/title').text

        return self.playlist_result(entries, collection_id, title_text)
