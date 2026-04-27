# coding: utf-8
from __future__ import unicode_literals
from __future__ import division

import base64
import binascii
import collections
import ctypes
import datetime
import email
import getpass
import io
import itertools
import optparse
import os
import platform
import re
import shlex
import socket
import struct
import subprocess
import sys
import types
import xml.etree.ElementTree

_IDENTITY = lambda x: x

# naming convention
# 'compat_' + Python3_name.replace('.', '_')
# other aliases exist for convenience and/or legacy
# wrap disposable test values in type() to reclaim storage

compat_str = str
compat_basestring = (str, bytes)
compat_chr = chr


compat_casefold = lambda s: s.casefold()


import collections.abc as compat_collections_abc


import urllib.request as compat_urllib_request


import urllib.error as compat_urllib_error


import urllib.parse as compat_urllib_parse

# unfavoured aliases
compat_urlparse = compat_urllib_parse
compat_urllib_parse_urlparse = compat_urllib_parse.urlparse


import urllib.response as compat_urllib_response


import http.cookiejar as compat_cookiejar
compat_http_cookiejar = compat_cookiejar
compat_cookiejar_Cookie = compat_cookiejar.Cookie
compat_http_cookiejar_Cookie = compat_cookiejar_Cookie


import http.cookies as compat_cookies
compat_http_cookies = compat_cookies
compat_cookies_SimpleCookie = compat_cookies.SimpleCookie
compat_http_cookies_SimpleCookie = compat_cookies_SimpleCookie


import html.entities as compat_html_entities
compat_html_entities_html5 = compat_html_entities.html5

import http.client as compat_http_client

from urllib.error import HTTPError as compat_HTTPError
compat_urllib_HTTPError = compat_HTTPError

from urllib.request import urlretrieve as compat_urlretrieve
compat_urllib_request_urlretrieve = compat_urlretrieve

from html.parser import HTMLParser as compat_HTMLParser


class compat_HTMLParseError(Exception):
    """Introduced for uniform cross-version exception handling; html.parser.HTMLParseError was removed in Py3.5."""
    pass


compat_html_parser_HTMLParser = compat_HTMLParser
compat_html_parser_HTMLParseError = compat_HTMLParseError


_DEVNULL = subprocess.DEVNULL
compat_subprocess_get_DEVNULL = lambda: _DEVNULL

import http.server as compat_http_server


from urllib.parse import unquote_to_bytes as compat_urllib_parse_unquote_to_bytes
from urllib.parse import unquote as compat_urllib_parse_unquote
from urllib.parse import unquote_plus as compat_urllib_parse_unquote_plus
from urllib.parse import urlencode as compat_urllib_parse_urlencode
from urllib.parse import parse_qs as compat_parse_qs


compat_urllib_parse_parse_qs = compat_parse_qs


from urllib.request import DataHandler as compat_urllib_request_DataHandler

from xml.etree.ElementTree import ParseError as compat_xml_parse_error
compat_xml_etree_ElementTree_ParseError = compat_xml_parse_error


# compat_xml_etree_ElementTree_Element
_etree = xml.etree.ElementTree


class _TreeBuilder(_etree.TreeBuilder):
    def doctype(self, name, pubid, system):
        pass


from xml.etree.ElementTree import Element as compat_etree_Element
compat_xml_etree_ElementTree_Element = compat_etree_Element


def compat_etree_fromstring(text):
    return _etree.XML(text, parser=_etree.XMLParser(target=_TreeBuilder()))


compat_etree_register_namespace = _etree.register_namespace
compat_xml_etree_register_namespace = compat_etree_register_namespace


# compat_xpath, compat_etree_iterfind
compat_etree_iterfind = lambda element, match: element.iterfind(match)
compat_xpath = _IDENTITY


# compat_os_name
compat_os_name = os._name if os.name == 'java' else os.name


# compat_shlex_quote
if compat_os_name == 'nt':
    def compat_shlex_quote(s):
        return s if re.match(r'^[-_\w./]+$', s) else '"%s"' % s.replace('"', '\\"')
else:
    try:
        from shlex import quote as compat_shlex_quote
    except ImportError:  # Python < 3.3
        def compat_shlex_quote(s):
            if re.match(r'^[-_\w./]+$', s):
                return s
            else:
                return "'" + s.replace("'", "'\"'\"'") + "'"


compat_shlex_split = shlex.split


def compat_ord(c):
    return c if isinstance(c, int) else ord(c)


compat_getenv = os.getenv
compat_expanduser = os.path.expanduser


def compat_setenv(key, value, env=os.environ):
    env[key] = value


compat_os_path_expanduser = compat_expanduser

compat_os_makedirs = os.makedirs

compat_realpath = os.path.realpath
compat_os_path_realpath = compat_realpath


def compat_print(s):
    assert isinstance(s, compat_str)
    print(s)


compat_getpass = getpass.getpass
compat_getpass_getpass = compat_getpass

compat_input = input

compat_kwargs = _IDENTITY

compat_numeric_types = (int, float, complex)
compat_integer_types = (int,)
compat_int = int

compat_socket_create_connection = socket.create_connection

from contextlib import suppress as compat_contextlib_suppress

compat_subprocess_Popen = subprocess.Popen


from shutil import get_terminal_size as compat_get_terminal_size
compat_shutil_get_terminal_size = compat_get_terminal_size

compat_itertools_count = itertools.count

from tokenize import tokenize as compat_tokenize_tokenize

compat_struct_pack = struct.pack
compat_struct_unpack = struct.unpack
compat_Struct = struct.Struct

compat_map = map
compat_filter = filter
compat_filter_fns = (filter,)
compat_zip = zip

from itertools import zip_longest as compat_itertools_zip_longest

from abc import ABC as compat_abc_ABC


# dict mixin used here
# like UserDict.DictMixin, without methods created by MutableMapping
class _DictMixin(compat_abc_ABC):
    def has_key(self, key):
        return key in self

    # get(), clear(), setdefault() in MM

    def iterkeys(self):
        return (k for k in self)

    def itervalues(self):
        return (self[k] for k in self)

    def iteritems(self):
        return ((k, self[k]) for k in self)

    # pop(), popitem() in MM

    def copy(self):
        return type(self)(self)

    # update() in MM


from collections import ChainMap as compat_collections_chain_map


# compat_re_Pattern, compat_re_Match
# Pythons disagree on the type of a pattern (RegexObject, _sre.SRE_Pattern, Pattern, ...?)
compat_re_Pattern = type(re.compile(''))
# and on the type of a match
compat_re_Match = type(re.match('a', 'a'))


compat_b64decode = base64.b64decode
compat_base64_b64decode = compat_b64decode


def compat_ctypes_WINFUNCTYPE(*args, **kwargs):
    return ctypes.WINFUNCTYPE(*args, **kwargs)


compat_open = open

compat_datetime_timedelta_total_seconds = datetime.timedelta.total_seconds


# optional decompression packages
# compat_brotli
# PyPi brotli package implements 'br' Content-Encoding
try:
    import brotli as compat_brotli
except ImportError:
    compat_brotli = None
# compat_ncompress
# PyPi ncompress package implements 'compress' Content-Encoding
try:
    import ncompress as compat_ncompress
except ImportError:
    compat_ncompress = None

# compat_zstandard
# PyPi zstandard package implements 'zstd' Content-Encoding (RFC 8878 7.2)
try:
    import zstandard as compat_zstandard
except ImportError:
    compat_zstandard = None


import _thread as compat_thread

compat_dict = compat_builtins_dict = dict
compat_dict_items = dict.items


legacy = [
    'compat_HTMLParseError',
    'compat_HTMLParser',
    'compat_HTTPError',
    'compat_b64decode',
    'compat_cookiejar',
    'compat_cookiejar_Cookie',
    'compat_cookies',
    'compat_cookies_SimpleCookie',
    'compat_etree_Element',
    'compat_etree_register_namespace',
    'compat_expanduser',
    'compat_getpass',
    'compat_parse_qs',
    'compat_realpath',
    'compat_shlex_split',
    'compat_urllib_parse_parse_qs',
    'compat_urllib_parse_unquote',
    'compat_urllib_parse_unquote_plus',
    'compat_urllib_parse_unquote_to_bytes',
    'compat_urllib_parse_urlencode',
    'compat_urllib_parse_urlparse',
    'compat_urlparse',
    'compat_urlretrieve',
    'compat_xml_parse_error',
]


__all__ = [
    'compat_Struct',
    'compat_abc_ABC',
    'compat_base64_b64decode',
    'compat_basestring',
    'compat_brotli',
    'compat_builtins_dict',
    'compat_casefold',
    'compat_chr',
    'compat_collections_abc',
    'compat_collections_chain_map',
    'compat_contextlib_suppress',
    'compat_ctypes_WINFUNCTYPE',
    'compat_datetime_timedelta_total_seconds',
    'compat_dict',
    'compat_dict_items',
    'compat_etree_fromstring',
    'compat_etree_iterfind',
    'compat_filter',
    'compat_filter_fns',
    'compat_get_terminal_size',
    'compat_getenv',
    'compat_getpass_getpass',
    'compat_html_entities',
    'compat_html_entities_html5',
    'compat_html_parser_HTMLParseError',
    'compat_html_parser_HTMLParser',
    'compat_http_cookiejar',
    'compat_http_cookiejar_Cookie',
    'compat_http_cookies',
    'compat_http_cookies_SimpleCookie',
    'compat_http_client',
    'compat_http_server',
    'compat_input',
    'compat_int',
    'compat_integer_types',
    'compat_itertools_count',
    'compat_itertools_zip_longest',
    'compat_kwargs',
    'compat_map',
    'compat_ncompress',
    'compat_numeric_types',
    'compat_open',
    'compat_ord',
    'compat_os_makedirs',
    'compat_os_name',
    'compat_os_path_expanduser',
    'compat_os_path_realpath',
    'compat_print',
    'compat_re_Match',
    'compat_re_Pattern',
    'compat_setenv',
    'compat_shlex_quote',
    'compat_shutil_get_terminal_size',
    'compat_socket_create_connection',
    'compat_str',
    'compat_struct_pack',
    'compat_struct_unpack',
    'compat_subprocess_get_DEVNULL',
    'compat_subprocess_Popen',
    'compat_thread',
    'compat_tokenize_tokenize',
    'compat_urllib_error',
    'compat_urllib_parse',
    'compat_urllib_request',
    'compat_urllib_request_DataHandler',
    'compat_urllib_response',
    'compat_urllib_request_urlretrieve',
    'compat_urllib_HTTPError',
    'compat_xml_etree_ElementTree_Element',
    'compat_xml_etree_ElementTree_ParseError',
    'compat_xml_etree_register_namespace',
    'compat_xpath',
    'compat_zip',
    'compat_zstandard',
]
