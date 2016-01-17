# coding: utf-8

from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import tr


class I18NTestIE(InfoExtractor):
    _VALID_URL = 'i18n:test'

    def _real_extract(self, url):
        self._downloader.to_screen(tr('I18N test message'))
