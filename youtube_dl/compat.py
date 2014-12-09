from __future__ import unicode_literals

import getpass
import optparse
import os
import re
import subprocess
import sys


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
    import http.cookiejar as compat_cookiejar
except ImportError:  # Python 2
    import cookielib as compat_cookiejar

try:
    import html.entities as compat_html_entities
except ImportError:  # Python 2
    import htmlentitydefs as compat_html_entities

try:
    import html.parser as compat_html_parser
except ImportError:  # Python 2
    import HTMLParser as compat_html_parser

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
    from urllib.parse import unquote as compat_urllib_parse_unquote
except ImportError:
    def compat_urllib_parse_unquote(string, encoding='utf-8', errors='replace'):
        if string == '':
            return string
        res = string.split('%')
        if len(res) == 1:
            return string
        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'replace'
        # pct_sequence: contiguous sequence of percent-encoded bytes, decoded
        pct_sequence = b''
        string = res[0]
        for item in res[1:]:
            try:
                if not item:
                    raise ValueError
                pct_sequence += item[:2].decode('hex')
                rest = item[2:]
                if not rest:
                    # This segment was just a single percent-encoded character.
                    # May be part of a sequence of code units, so delay decoding.
                    # (Stored in pct_sequence).
                    continue
            except ValueError:
                rest = '%' + item
            # Encountered non-percent-encoded characters. Flush the current
            # pct_sequence.
            string += pct_sequence.decode(encoding, errors) + rest
            pct_sequence = b''
        if pct_sequence:
            # Flush the final pct_sequence
            string += pct_sequence.decode(encoding, errors)
        return string


try:
    from urllib.parse import parse_qs as compat_parse_qs
except ImportError:  # Python 2
    # HACK: The following is the correct parse_qs implementation from cpython 3's stdlib.
    # Python 2's version is apparently totally broken

    def _parse_qsl(qs, keep_blank_values=False, strict_parsing=False,
                   encoding='utf-8', errors='replace'):
        qs, _coerce_result = qs, unicode
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
    compat_str = unicode  # Python 2
except NameError:
    compat_str = str

try:
    compat_chr = unichr  # Python 2
except NameError:
    compat_chr = chr

try:
    from xml.etree.ElementTree import ParseError as compat_xml_parse_error
except ImportError:  # Python 2.6
    from xml.parsers.expat import ExpatError as compat_xml_parse_error

try:
    from shlex import quote as shlex_quote
except ImportError:  # Python < 3.3
    def shlex_quote(s):
        if re.match(r'^[-_\w./]+$', s):
            return s
        else:
            return "'" + s.replace("'", "'\"'\"'") + "'"


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
    (lambda x: x)(**{'x': 0})
except TypeError:
    def compat_kwargs(kwargs):
        return dict((bytes(k), v) for k, v in kwargs.items())
else:
    compat_kwargs = lambda kwargs: kwargs


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


__all__ = [
    'compat_HTTPError',
    'compat_chr',
    'compat_cookiejar',
    'compat_expanduser',
    'compat_getenv',
    'compat_getpass',
    'compat_html_entities',
    'compat_html_parser',
    'compat_http_client',
    'compat_kwargs',
    'compat_ord',
    'compat_parse_qs',
    'compat_print',
    'compat_str',
    'compat_subprocess_get_DEVNULL',
    'compat_urllib_error',
    'compat_urllib_parse',
    'compat_urllib_parse_unquote',
    'compat_urllib_parse_urlparse',
    'compat_urllib_request',
    'compat_urlparse',
    'compat_urlretrieve',
    'compat_xml_parse_error',
    'shlex_quote',
    'subprocess_check_output',
    'workaround_optparse_bug9161',
]
