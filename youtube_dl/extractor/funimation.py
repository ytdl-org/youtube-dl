# coding: utf-8
from __future__ import unicode_literals
from .common import InfoExtractor
from ..compat import compat_HTTPError
from ..utils import (
    encode_dict,
    sanitized_Request,
    ExtractorError,
    urlencode_postdata
)
import re

class FunimationIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funimation\.com/shows/.+[^ ]/videos/official/(?P<id>[^?]+)'

    _TEST = {
        'url': 'http://www.funimation.com/shows/air/videos/official/breeze',
        'info_dict': {
            'id': 'AIRENG0001',
            'title': 'Air - 1 - Breeze ',
            'ext': 'mp4',
            'thumbnail': 'http://www.funimation.com/admin/uploads/default/recap_thumbnails/7555590/home_spotlight/AIR0001.jpg',
            'description': 'Travelling puppeteer Yukito arrives in a small town where he hopes to earn money through the magic of his puppets. When a young girl named Misuzu lures him to her home with the promise of food, his life changes forever. ',
        }
    }

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return
        login_url = 'http://www.funimation.com/login'
        data = urlencode_postdata(encode_dict({
            'loginForm2': 'loginform',
            'email_field': username,
            'password_field': password,
        }))
        login_request = sanitized_Request(login_url, data)
        login_request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        try:
            login = self._download_webpage(login_request, login_url)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                raise ExtractorError('Funimation is not available in your region.', expected=True)
            raise
        if re.search(r'<meta property="og:url" content="http://www.funimation.com/login"/>', login) is not None:
                raise ExtractorError('Unable to login, wrong username or password.', expected=True)

    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        try:
            webpage = self._download_webpage(url, video_id)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                raise ExtractorError('Funimation is not available in your region.', expected=True)
            raise
        if re.search(r'"sdUrl":"http', webpage) is None:
                raise ExtractorError('You are not logged-in or the stream requires subscription.', expected=True)

        m3u8 = self._search_regex(r'".+Url":"(.+?m3u8)"', webpage, 'm3u8') + self._search_regex(r'"authToken":"(.+?)"', webpage, 'm3u8')
        formats = self._extract_m3u8_formats(m3u8.replace('\\', ''), video_id, ext='mp4', entry_protocol='m3u8_native')

        video_show = self._search_regex(r'"artist":"(.+?)"', webpage, 'video_show')
        video_track = self._search_regex(r'"videoNumber":"(\d+).0"', webpage, 'video_track')
        video_title = self._search_regex(r'"title":"({0}.+?)"'.format(video_track), webpage, 'video_title')
        video_id = self._search_regex(r'"FUNImationID":"(.+?)"', webpage, 'video_id')

        return {
            'id': video_id,
            'title': video_show + ' - ' + video_title + ' ',
            'formats': formats,
            'thumbnail': self._og_search_thumbnail(webpage),
            'description': self._og_search_description(webpage)
        }
