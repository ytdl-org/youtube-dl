from __future__ import unicode_literals

import binascii
import collections
import email
import getpass
import io
import optparse
import os
import re
import shlex
import shutil
import socket
import subprocess
import sys
import itertools
import xml.etree.ElementTree


try:
    import urllib.request as compat_urllib_request
except ImportError:  # Python 2
    import urllib2 as compat_urllib_request

try:
    import urllib.error as compat_urllib_error
except ImportError:  # Python 2
    import urllib2 as compat_urllib_error

try:
    import urllib.parse as compat_urllib_parse
except ImportError:  # Python 2
    import urllib as compat_urllib_parse

try:
    from urllib.parse import urlparse as compat_urllib_parse_urlparse
except ImportError:  # Python 2
    from urlparse import urlparse as compat_urllib_parse_urlparse

try:
    import urllib.parse as compat_urlparse
except ImportError:  # Python 2
    import urlparse as compat_urlparse

try:
    import urllib.response as compat_urllib_response
except ImportError:  # Python 2
    import urllib as compat_urllib_response

try:
    import http.cookiejar as compat_cookiejar
except ImportError:  # Python 2
    import cookielib as compat_cookiejar

try:
    import http.cookies as compat_cookies
except ImportError:  # Python 2
    import Cookie as compat_cookies

try:
    import html.entities as compat_html_entities
except ImportError:  # Python 2
    import htmlentitydefs as compat_html_entities

try:
    import http.client as compat_http_client
except ImportError:  # Python 2
    import httplib as compat_http_client

try:
    from urllib.error import HTTPError as compat_HTTPError
except ImportError:  # Python 2
    from urllib2 import HTTPError as compat_HTTPError

try:
    from urllib.request import urlretrieve as compat_urlretrieve
except ImportError:  # Python 2
    from urllib import urlretrieve as compat_urlretrieve


try:
    from subprocess import DEVNULL
    compat_subprocess_get_DEVNULL = lambda: DEVNULL
except ImportError:
    compat_subprocess_get_DEVNULL = lambda: open(os.path.devnull, 'w')

try:
    import http.server as compat_http_server
except ImportError:
    import BaseHTTPServer as compat_http_server

try:
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str

try:
    from urllib.parse import unquote_to_bytes as compat_urllib_parse_unquote_to_bytes
    from urllib.parse import unquote as compat_urllib_parse_unquote
    from urllib.parse import unquote_plus as compat_urllib_parse_unquote_plus
except ImportError:  # Python 2
    _asciire = (compat_urllib_parse._asciire if hasattr(compat_urllib_parse, '_asciire')
                else re.compile('([\x00-\x7f]+)'))

    # HACK: The following are the correct unquote_to_bytes, unquote and unquote_plus
    # implementations from cpython 3.4.3's stdlib. Python 2's version
    # is apparently broken (see https://github.com/rg3/youtube-dl/pull/6244)

    def compat_urllib_parse_unquote_to_bytes(string):
        """unquote_to_bytes('abc%20def') -> b'abc def'."""
        # Note: strings are encoded as UTF-8. This is only an issue if it contains
        # unescaped non-ASCII characters, which URIs should not.
        if not string:
            # Is it a string-like object?
            string.split
            return b''
        if isinstance(string, compat_str):
            string = string.encode('utf-8')
        bits = string.split(b'%')
        if len(bits) == 1:
            return string
        res = [bits[0]]
        append = res.append
        for item in bits[1:]:
            try:
                append(compat_urllib_parse._hextochr[item[:2]])
                append(item[2:])
            except KeyError:
                append(b'%')
                append(item)
        return b''.join(res)

    def compat_urllib_parse_unquote(string, encoding='utf-8', errors='replace'):
        """Replace %xx escapes by their single-character equivalent. The optional
        encoding and errors parameters specify how to decode percent-encoded
        sequences into Unicode characters, as accepted by the bytes.decode()
        method.
        By default, percent-encoded sequences are decoded with UTF-8, and invalid
        sequences are replaced by a placeholder character.

        unquote('abc%20def') -> 'abc def'.
        """
        if '%' not in string:
            string.split
            return string
        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'replace'
        bits = _asciire.split(string)
        res = [bits[0]]
        append = res.append
        for i in range(1, len(bits), 2):
            append(compat_urllib_parse_unquote_to_bytes(bits[i]).decode(encoding, errors))
            append(bits[i + 1])
        return ''.join(res)

    def compat_urllib_parse_unquote_plus(string, encoding='utf-8', errors='replace'):
        """Like unquote(), but also replace plus signs by spaces, as required for
        unquoting HTML form values.

        unquote_plus('%7e/abc+def') -> '~/abc def'
        """
        string = string.replace('+', ' ')
        return compat_urllib_parse_unquote(string, encoding, errors)

try:
    from urllib.request import DataHandler as compat_urllib_request_DataHandler
except ImportError:  # Python < 3.4
    # Ported from CPython 98774:1733b3bd46db, Lib/urllib/request.py
    class compat_urllib_request_DataHandler(compat_urllib_request.BaseHandler):
        def data_open(self, req):
            # data URLs as specified in RFC 2397.
            #
            # ignores POSTed data
            #
            # syntax:
            # dataurl   := "data:" [ mediatype ] [ ";base64" ] "," data
            # mediatype := [ type "/" subtype ] *( ";" parameter )
            # data      := *urlchar
            # parameter := attribute "=" value
            url = req.get_full_url()

            scheme, data = url.split(":", 1)
            mediatype, data = data.split(",", 1)

            # even base64 encoded data URLs might be quoted so unquote in any case:
            data = compat_urllib_parse_unquote_to_bytes(data)
            if mediatype.endswith(";base64"):
                data = binascii.a2b_base64(data)
                mediatype = mediatype[:-7]

            if not mediatype:
                mediatype = "text/plain;charset=US-ASCII"

            headers = email.message_from_string(
                "Content-type: %s\nContent-length: %d\n" % (mediatype, len(data)))

            return compat_urllib_response.addinfourl(io.BytesIO(data), headers, url)

try:
    compat_basestring = basestring  # Python 2
except NameError:
    compat_basestring = str

try:
    compat_chr = unichr  # Python 2
except NameError:
    compat_chr = chr

try:
    from xml.etree.ElementTree import ParseError as compat_xml_parse_error
except ImportError:  # Python 2.6
    from xml.parsers.expat import ExpatError as compat_xml_parse_error

if sys.version_info[0] >= 3:
    compat_etree_fromstring = xml.etree.ElementTree.fromstring
else:
    # python 2.x tries to encode unicode strings with ascii (see the
    # XMLParser._fixtext method)
    etree = xml.etree.ElementTree

    try:
        _etree_iter = etree.Element.iter
    except AttributeError:  # Python <=2.6
        def _etree_iter(root):
            for el in root.findall('*'):
                yield el
                for sub in _etree_iter(el):
                    yield sub

    # on 2.6 XML doesn't have a parser argument, function copied from CPython
    # 2.7 source
    def _XML(text, parser=None):
        if not parser:
            parser = etree.XMLParser(target=etree.TreeBuilder())
        parser.feed(text)
        return parser.close()

    def _element_factory(*args, **kwargs):
        el = etree.Element(*args, **kwargs)
        for k, v in el.items():
            if isinstance(v, bytes):
                el.set(k, v.decode('utf-8'))
        return el

    def compat_etree_fromstring(text):
        doc = _XML(text, parser=etree.XMLParser(target=etree.TreeBuilder(element_factory=_element_factory)))
        for el in _etree_iter(doc):
            if el.text is not None and isinstance(el.text, bytes):
                el.text = el.text.decode('utf-8')
        return doc

try:
    from urllib.parse import parse_qs as compat_parse_qs
except ImportError:  # Python 2
    # HACK: The following is the correct parse_qs implementation from cpython 3's stdlib.
    # Python 2's version is apparently totally broken

    def _parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
                   encoding='utf-8', errors='replace'):
        qs, _coerce_result = qs, compat_str
        pairs = [s2 for s1 in qs.split('&') for s2 in s1.split(';')]
        r = []
        for name_value in pairs:
            if not name_value and not strict_parsing:
                continue
            nv = name_value.split('=', 1)
            if len(nv) != 2:
                if strict_parsing:
                    raise ValueError("bad query field: %r" % (name_value,))
                # Handle case of a control-name with no equal sign
                if keep_blank_values:
                    nv.append('')
                else:
                    continue
            if len(nv[1]) or keep_blank_values:
                name = nv[0].replace('+', ' ')
                name = compat_urllib_parse_unquote(
                    name, encoding=encoding, errors=errors)
                name = _coerce_result(name)
                value = nv[1].replace('+', ' ')
                value = compat_urllib_parse_unquote(
                    value, encoding=encoding, errors=errors)
                value = _coerce_result(value)
                r.append((name, value))
        return r

    def compat_parse_qs(qs, keep_blank_values=False, strict_parsing=False,
                        encoding='utf-8', errors='replace'):
        parsed_result = {}
        pairs = _parse_qsl(qs, keep_blank_values, strict_parsing,
                           encoding=encoding, errors=errors)
        for name, value in pairs:
            if name in parsed_result:
                parsed_result[name].append(value)
            else:
                parsed_result[name] = [value]
        return parsed_result

try:
    from shlex import quote as shlex_quote
except ImportError:  # Python < 3.3
    def shlex_quote(s):
        if re.match(r'^[-_\w./]+$', s):
            return s
        else:
            return "'" + s.replace("'", "'\"'\"'") + "'"


if sys.version_info >= (2, 7, 3):
    compat_shlex_split = shlex.split
else:
    # Working around shlex issue with unicode strings on some python 2
    # versions (see http://bugs.python.org/issue1548891)
    def compat_shlex_split(s, comments=False, posix=True):
        if isinstance(s, compat_str):
            s = s.encode('utf-8')
        return shlex.split(s, comments, posix)


def compat_ord(c):
    if type(c) is int:
        return c
    else:
        return ord(c)


if sys.version_info >= (3, 0):
    compat_getenv = os.getenv
    compat_expanduser = os.path.expanduser
else:
    # Environment variables should be decoded with filesystem encoding.
    # Otherwise it will fail if any non-ASCII characters present (see #3854 #3217 #2918)

    def compat_getenv(key, default=None):
        from .utils import get_filesystem_encoding
        env = os.getenv(key, default)
        if env:
            env = env.decode(get_filesystem_encoding())
        return env

    # HACK: The default implementations of os.path.expanduser from cpython do not decode
    # environment variables with filesystem encoding. We will work around this by
    # providing adjusted implementations.
    # The following are os.path.expanduser implementations from cpython 2.7.8 stdlib
    # for different platforms with correct environment variables decoding.

    if os.name == 'posix':
        def compat_expanduser(path):
            """Expand ~ and ~user constructions.  If user or $HOME is unknown,
            do nothing."""
            if not path.startswith('~'):
                return path
            i = path.find('/', 1)
            if i < 0:
                i = len(path)
            if i == 1:
                if 'HOME' not in os.environ:
                    import pwd
                    userhome = pwd.getpwuid(os.getuid()).pw_dir
                else:
                    userhome = compat_getenv('HOME')
            else:
                import pwd
                try:
                    pwent = pwd.getpwnam(path[1:i])
                except KeyError:
                    return path
                userhome = pwent.pw_dir
            userhome = userhome.rstrip('/')
            return (userhome + path[i:]) or '/'
    elif os.name == 'nt' or os.name == 'ce':
        def compat_expanduser(path):
            """Expand ~ and ~user constructs.

            If user or $HOME is unknown, do nothing."""
            if path[:1] != '~':
                return path
            i, n = 1, len(path)
            while i < n and path[i] not in '/\\':
                i = i + 1

            if 'HOME' in os.environ:
                userhome = compat_getenv('HOME')
            elif 'USERPROFILE' in os.environ:
                userhome = compat_getenv('USERPROFILE')
            elif 'HOMEPATH' not in os.environ:
                return path
            else:
                try:
                    drive = compat_getenv('HOMEDRIVE')
                except KeyError:
                    drive = ''
                userhome = os.path.join(drive, compat_getenv('HOMEPATH'))

            if i != 1:  # ~user
                userhome = os.path.join(os.path.dirname(userhome), path[1:i])

            return userhome + path[i:]
    else:
        compat_expanduser = os.path.expanduser


if sys.version_info < (3, 0):
    def compat_print(s):
        from .utils import preferredencoding
        print(s.encode(preferredencoding(), 'xmlcharrefreplace'))
else:
    def compat_print(s):
        assert isinstance(s, compat_str)
        print(s)


try:
    subprocess_check_output = subprocess.check_output
except AttributeError:
    def subprocess_check_output(*args, **kwargs):
        assert 'input' not in kwargs
        p = subprocess.Popen(*args, stdout=subprocess.PIPE, **kwargs)
        output, _ = p.communicate()
        ret = p.poll()
        if ret:
            raise subprocess.CalledProcessError(ret, p.args, output=output)
        return output

if sys.version_info < (3, 0) and sys.platform == 'win32':
    def compat_getpass(prompt, *args, **kwargs):
        if isinstance(prompt, compat_str):
            from .utils import preferredencoding
            prompt = prompt.encode(preferredencoding())
        return getpass.getpass(prompt, *args, **kwargs)
else:
    compat_getpass = getpass.getpass

# Old 2.6 and 2.7 releases require kwargs to be bytes
try:
    def _testfunc(x):
        pass
    _testfunc(**{'x': 0})
except TypeError:
    def compat_kwargs(kwargs):
        return dict((bytes(k), v) for k, v in kwargs.items())
else:
    compat_kwargs = lambda kwargs: kwargs


if sys.version_info < (2, 7):
    def compat_socket_create_connection(address, timeout, source_address=None):
        host, port = address
        err = None
        for res in socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                sock.settimeout(timeout)
                if source_address:
                    sock.bind(source_address)
                sock.connect(sa)
                return sock
            except socket.error as _:
                err = _
                if sock is not None:
                    sock.close()
        if err is not None:
            raise err
        else:
            raise socket.error("getaddrinfo returns an empty list")
else:
    compat_socket_create_connection = socket.create_connection


# Fix https://github.com/rg3/youtube-dl/issues/4223
# See http://bugs.python.org/issue9161 for what is broken
def workaround_optparse_bug9161():
    op = optparse.OptionParser()
    og = optparse.OptionGroup(op, 'foo')
    try:
        og.add_option('-t')
    except TypeError:
        real_add_option = optparse.OptionGroup.add_option

        def _compat_add_option(self, *args, **kwargs):
            enc = lambda v: (
                v.encode('ascii', 'replace') if isinstance(v, compat_str)
                else v)
            bargs = [enc(a) for a in args]
            bkwargs = dict(
                (k, enc(v)) for k, v in kwargs.items())
            return real_add_option(self, *bargs, **bkwargs)
        optparse.OptionGroup.add_option = _compat_add_option

if hasattr(shutil, 'get_terminal_size'):  # Python >= 3.3
    compat_get_terminal_size = shutil.get_terminal_size
else:
    _terminal_size = collections.namedtuple('terminal_size', ['columns', 'lines'])

    def compat_get_terminal_size(fallback=(80, 24)):
        columns = compat_getenv('COLUMNS')
        if columns:
            columns = int(columns)
        else:
            columns = None
        lines = compat_getenv('LINES')
        if lines:
            lines = int(lines)
        else:
            lines = None

        if columns is None or lines is None or columns <= 0 or lines <= 0:
            try:
                sp = subprocess.Popen(
                    ['stty', 'size'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = sp.communicate()
                _lines, _columns = map(int, out.split())
            except Exception:
                _columns, _lines = _terminal_size(*fallback)

            if columns is None or columns <= 0:
                columns = _columns
            if lines is None or lines <= 0:
                lines = _lines
        return _terminal_size(columns, lines)

try:
    itertools.count(start=0, step=1)
    compat_itertools_count = itertools.count
except TypeError:  # Python 2.6
    def compat_itertools_count(start=0, step=1):
        n = start
        while True:
            yield n
            n += step

if sys.version_info >= (3, 0):
    from tokenize import tokenize as compat_tokenize_tokenize
else:
    from tokenize import generate_tokens as compat_tokenize_tokenize

__all__ = [
    'compat_HTTPError',
    'compat_basestring',
    'compat_chr',
    'compat_cookiejar',
    'compat_cookies',
    'compat_etree_fromstring',
    'compat_expanduser',
    'compat_get_terminal_size',
    'compat_getenv',
    'compat_getpass',
    'compat_html_entities',
    'compat_http_client',
    'compat_http_server',
    'compat_itertools_count',
    'compat_kwargs',
    'compat_ord',
    'compat_parse_qs',
    'compat_print',
    'compat_shlex_split',
    'compat_socket_create_connection',
    'compat_str',
    'compat_subprocess_get_DEVNULL',
    'compat_tokenize_tokenize',
    'compat_urllib_error',
    'compat_urllib_parse',
    'compat_urllib_parse_unquote',
    'compat_urllib_parse_unquote_plus',
    'compat_urllib_parse_unquote_to_bytes',
    'compat_urllib_parse_urlparse',
    'compat_urllib_request',
    'compat_urllib_request_DataHandler',
    'compat_urllib_response',
    'compat_urlparse',
    'compat_urlretrieve',
    'compat_xml_parse_error',
    'shlex_quote',
    'subprocess_check_output',
    'workaround_optparse_bug9161',
]
