# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    sanitized_Request,
    urlencode_postdata,
)


class ArretSurImagesIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?arretsurimages\.net/emissions/.*?-id(?P<id>[0-9]+)'
    _LOGIN_URL = 'https://www.arretsurimages.net/forum/login.php'
    _DOWNLOAD_URL = 'https?://v42.arretsurimages.net'
    _FILE_URL = 'https?://v42.arretsurimages.net/fichiers'

    _TEST = {
        'url': 'https://www.arretsurimages.net/emissions/2017-02-17/Theo-La-matraque-telescopique-beaucoup-de-collegues-l-ont-demandee-id9557',
        'md5': '650d2102dad67b2b6a94ac9c063f6d5b',
        'info_dict': {
            'id': '9557',
            'ext': 'mp4',
            'title': 'Théo : "La matraque télescopique, beaucoup de collègues l\'ont demandée"',
        },
        'skip': 'Requires account credentials',
    }

    def _real_initialize(self):
        self._login()

    def _login(self):
        (username, password) = self._get_login_info()
        if username is None:
            return

        login_data = urlencode_postdata(self._get_login_data(username, password))

        login_results = self._download_webpage(
            sanitized_Request(self._LOGIN_URL, login_data),
            None, note='Logging in', errnote='Unable to log in')

        if not self._is_logged(login_results):
            self._downloader.report_warning('unable to log in: bad username or password')
            return False

        return True

    def _is_logged(self, login_results):
        return re.search(r'(?i)Ce nom d\'utilisateur / mot de passe est introuvable ou inactif. Recommencez', login_results) is None

    def _get_login_data(self, username, password):
        return {
            'ok': 'Valider',
            'username': username,
            'password': password,
        }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)
        video_title = self._html_search_regex(
            r'<h1 itemprop=".*?">(.*?)</h1>',
            webpage, 'title')
        download_url = self._html_search_regex(
            r'<a href="(' + self._DOWNLOAD_URL + '/telecharger/.*?.mp4)"',
            webpage, 'download information')

        download_page = self._download_webpage(download_url, video_id, 'Downloading download information page')
        video_url = self._html_search_regex(
            r'<a id="file" href="(' + self._FILE_URL + '/.*?.mp4)" download>suivre ce lien</a>',
            download_page, 'video url')

        return {
            'id': video_id,
            'title': video_title,
            'url': video_url,
        }


class HorsSerieIE(ArretSurImagesIE):
    _VALID_URL = r'https?://(?:www\.)?hors-serie\.net/.*?-id(?P<id>[0-9]+)'
    _LOGIN_URL = 'https://www.hors-serie.net/connexion.php'
    _DOWNLOAD_URL = 'https?://v42.hors-serie.net'
    _FILE_URL = 'https?://v42.hors-serie.net/fichiers_hs'

    _TEST = {
        'url': 'http://www.hors-serie.net/Dans-le-Texte/2017-01-21/L-effondrement-qui-vient-id211',
        'md5': 'a6aabfe23871146fb55c924e196680c2',
        'info_dict': {
            'id': '211',
            'ext': 'mp4',
            'title': 'L\'effondrement qui vient',
        },
        'skip': 'Requires account credentials',
    }

    def _get_login_data(self, username, password):
        return {
            'submit': 'valider',
            'mail': username,
            'pass': password,
        }

    def _is_logged(self, login_results):
        return re.search(r'(?i)Adresse électronique ou mot de passe invalide...', login_results) is None
