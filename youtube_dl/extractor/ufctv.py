# coding: utf-8
from __future__ import unicode_literals

from .imggaming import ImgGamingBaseIE


class UFCTVIE(ImgGamingBaseIE):
    _VALID_URL = ImgGamingBaseIE._VALID_URL_TEMPL % r'(?:www\.)?ufc\.tv'
    _NETRC_MACHINE = 'ufctv'
    _DOMAIN = 'ufc.tv'
    _REALM = 'ufc'


class UFCArabiaIE(ImgGamingBaseIE):
    _VALID_URL = ImgGamingBaseIE._VALID_URL_TEMPL % r'app\.ufcarabia\.com'
    _NETRC_MACHINE = 'ufcarabia'
    _DOMAIN = 'app.ufcarabia.com'
    _REALM = 'admufc'
