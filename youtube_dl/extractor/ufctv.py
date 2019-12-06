# coding: utf-8
from __future__ import unicode_literals

from .imggaming import ImgGamingBaseIE


class UFCTVIE(ImgGamingBaseIE):
    _VALID_URL = ImgGamingBaseIE._VALID_URL_TEMPL % r'(?:ufc\.tv|(?:ufc)?fightpass\.com)'
    _NETRC_MACHINE = 'ufctv'
    _REALM = 'ufc'


class UFCArabiaIE(ImgGamingBaseIE):
    _VALID_URL = ImgGamingBaseIE._VALID_URL_TEMPL % r'ufcarabia\.(?:ae|com)'
    _NETRC_MACHINE = 'ufcarabia'
    _REALM = 'admufc'
