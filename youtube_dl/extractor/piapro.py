# coding: utf-8

from __future__ import unicode_literals
from .common import InfoExtractor
from ..compat import compat_urlparse
from ..utils import urlencode_postdata, ExtractorError


class PiaproExtractorIE(InfoExtractor):
    _LOGIN_URL = "https://piapro.jp/login/"
    _LOGIN_REQUIRED = False
    IE_NAME = "piapro"
    IE_DESC = "piapro"
    _NETRC_MACHINE = "piapro"
    _VALID_URL = r'(https?:\/\/)??piapro\.jp\/t\/(?P<id>\w+)\/?'
    _TEST = {
        'url': 'https://piapro.jp/t/NXYR',
        'md5': 'a9d52f27d13bafab7ee34116a7dcfa77',
        'info_dict': {
            'id': 'NXYR',
            'ext': 'mp3',
            'title': '裏表ラバーズ',
            'thumbnail': r're:^https?://.*\.jpg$',
        }
    }

    def _real_initialize(self):
        self._login_status = self._login()

    def _login(self):
        username, password = self._get_login_info()
        if not username:
            return False
        login_ok = True
        login_form_strs = {
            '_username': username,
            '_password': password,
            '_remember_me': 'on',
            'login': 'ログイン'
        }
        self._request_webpage(self._LOGIN_URL, None)
        urlh = self._request_webpage(
            'https://piapro.jp/login/exe', None,
            note='Logging in', errnote='Unable to log in',
            data=urlencode_postdata(login_form_strs))
        if urlh is False:
            login_ok = False
        else:
            parts = compat_urlparse.urlparse(urlh.geturl())
            if parts.path != '/':
                login_ok = False
        if not login_ok:
            self._downloader.report_warning(
                'unable to log in: bad username or password')
        return login_ok

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        catId = self._search_regex(r'categoryId=(.+)">', webpage, None)
        is_music = int(catId) in [1, 2, 21, 22, 23, 24, 25]
        if not is_music:
            raise ExtractorError(
                "It's not music.", expected=True, video_id=video_id)
        title = self._html_search_regex(
            r'<h1 class="cd_works-title">(.+?)</h1>', webpage, 'title')
        uploader = self._search_regex(
            r'<a class="cd_user-name" href="/.*">([^<]+)さん<', webpage, None)
        contentId = self._html_search_regex(
            r'contentId\:\'(.+)\'', webpage, None)
        createDate = self._html_search_regex(
            r'createDate\:\'(.+)\'', webpage, None)
        player_url = "https://piapro.jp/html5_player_popup/?id={cid}&cdate={cdate}".format(
            cid=contentId, cdate=createDate)
        player_webpage = self._download_webpage(player_url, "Player")
        mp3_url = self._html_search_regex(
            r'mp3: \'(?P<url>.*?)\'\}', player_webpage, 'url', group='url')
        info = {
            'id': video_id,
            'title': title,
            'uploader': uploader,
            'formats': [{
                'format_id': "player_mp3",
                'url': mp3_url,
                'ext': "mp3",
                'vcodec': "none",
            }]
        }
        return info
