#!/usr/bin/env python
# -*- coding: utf-8 -*-

import contextlib
import ctypes
import datetime
import email.utils
import errno
import getpass
import gzip
import itertools
import io
import json
import locale
import math
import os
import pipes
import platform
import re
import ssl
import socket
import struct
import subprocess
import sys
import traceback
import xml.etree.ElementTree
import zlib

try:
    import urllib.request as compat_urllib_request
except ImportError: # Python 2
    import urllib2 as compat_urllib_request

try:
    import urllib.error as compat_urllib_error
except ImportError: # Python 2
    import urllib2 as compat_urllib_error

try:
    import urllib.parse as compat_urllib_parse
except ImportError: # Python 2
    import urllib as compat_urllib_parse

try:
    from urllib.parse import urlparse as compat_urllib_parse_urlparse
except ImportError: # Python 2
    from urlparse import urlparse as compat_urllib_parse_urlparse

try:
    import urllib.parse as compat_urlparse
except ImportError: # Python 2
    import urlparse as compat_urlparse

try:
    import http.cookiejar as compat_cookiejar
except ImportError: # Python 2
    import cookielib as compat_cookiejar

try:
    import html.entities as compat_html_entities
except ImportError: # Python 2
    import htmlentitydefs as compat_html_entities

try:
    import html.parser as compat_html_parser
except ImportError: # Python 2
    import HTMLParser as compat_html_parser

try:
    import http.client as compat_http_client
except ImportError: # Python 2
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
    from urllib.parse import parse_qs as compat_parse_qs
except ImportError: # Python 2
    # HACK: The following is the correct parse_qs implementation from cpython 3's stdlib.
    # Python 2's version is apparently totally broken
    def _unquote(string, encoding='utf-8', errors='replace'):
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
                name = _unquote(name, encoding=encoding, errors=errors)
                name = _coerce_result(name)
                value = nv[1].replace('+', ' ')
                value = _unquote(value, encoding=encoding, errors=errors)
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
    compat_str = unicode # Python 2
except NameError:
    compat_str = str

try:
    compat_chr = unichr # Python 2
except NameError:
    compat_chr = chr

try:
    from xml.etree.ElementTree import ParseError as compat_xml_parse_error
except ImportError:  # Python 2.6
    from xml.parsers.expat import ExpatError as compat_xml_parse_error

def compat_ord(c):
    if type(c) is int: return c
    else: return ord(c)

# This is not clearly defined otherwise
compiled_regex_type = type(re.compile(''))

std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0 (Chrome)',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-us,en;q=0.5',
}

def preferredencoding():
    """Get preferred encoding.

    Returns the best encoding scheme for the system, based on
    locale.getpreferredencoding() and some further tweaks.
    """
    try:
        pref = locale.getpreferredencoding()
        u'TEST'.encode(pref)
    except:
        pref = 'UTF-8'

    return pref

if sys.version_info < (3,0):
    def compat_print(s):
        print(s.encode(preferredencoding(), 'xmlcharrefreplace'))
else:
    def compat_print(s):
        assert type(s) == type(u'')
        print(s)

# In Python 2.x, json.dump expects a bytestream.
# In Python 3.x, it writes to a character stream
if sys.version_info < (3,0):
    def write_json_file(obj, fn):
        with open(fn, 'wb') as f:
            json.dump(obj, f)
else:
    def write_json_file(obj, fn):
        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(obj, f)

if sys.version_info >= (2,7):
    def find_xpath_attr(node, xpath, key, val):
        """ Find the xpath xpath[@key=val] """
        assert re.match(r'^[a-zA-Z]+$', key)
        assert re.match(r'^[a-zA-Z0-9@\s:._]*$', val)
        expr = xpath + u"[@%s='%s']" % (key, val)
        return node.find(expr)
else:
    def find_xpath_attr(node, xpath, key, val):
        for f in node.findall(xpath):
            if f.attrib.get(key) == val:
                return f
        return None

# On python2.6 the xml.etree.ElementTree.Element methods don't support
# the namespace parameter
def xpath_with_ns(path, ns_map):
    components = [c.split(':') for c in path.split('/')]
    replaced = []
    for c in components:
        if len(c) == 1:
            replaced.append(c[0])
        else:
            ns, tag = c
            replaced.append('{%s}%s' % (ns_map[ns], tag))
    return '/'.join(replaced)

def htmlentity_transform(matchobj):
    """Transforms an HTML entity to a character.

    This function receives a match object and is intended to be used with
    the re.sub() function.
    """
    entity = matchobj.group(1)

    # Known non-numeric HTML entity
    if entity in compat_html_entities.name2codepoint:
        return compat_chr(compat_html_entities.name2codepoint[entity])

    mobj = re.match(u'(?u)#(x?\\d+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith(u'x'):
            base = 16
            numstr = u'0%s' % numstr
        else:
            base = 10
        return compat_chr(int(numstr, base))

    # Unknown entity in name, return its literal representation
    return (u'&%s;' % entity)

compat_html_parser.locatestarttagend = re.compile(r"""<[a-zA-Z][-.a-zA-Z0-9:_]*(?:\s+(?:(?<=['"\s])[^\s/>][^\s/=>]*(?:\s*=+\s*(?:'[^']*'|"[^"]*"|(?!['"])[^>\s]*))?\s*)*)?\s*""", re.VERBOSE) # backport bugfix
class BaseHTMLParser(compat_html_parser.HTMLParser):
    def __init(self):
        compat_html_parser.HTMLParser.__init__(self)
        self.html = None

    def loads(self, html):
        self.html = html
        self.feed(html)
        self.close()

class AttrParser(BaseHTMLParser):
    """Modified HTMLParser that isolates a tag with the specified attribute"""
    def __init__(self, attribute, value):
        self.attribute = attribute
        self.value = value
        self.result = None
        self.started = False
        self.depth = {}
        self.watch_startpos = False
        self.error_count = 0
        BaseHTMLParser.__init__(self)

    def error(self, message):
        if self.error_count > 10 or self.started:
            raise compat_html_parser.HTMLParseError(message, self.getpos())
        self.rawdata = '\n'.join(self.html.split('\n')[self.getpos()[0]:]) # skip one line
        self.error_count += 1
        self.goahead(1)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.started:
            self.find_startpos(None)
        if self.attribute in attrs and attrs[self.attribute] == self.value:
            self.result = [tag]
            self.started = True
            self.watch_startpos = True
        if self.started:
            if not tag in self.depth: self.depth[tag] = 0
            self.depth[tag] += 1

    def handle_endtag(self, tag):
        if self.started:
            if tag in self.depth: self.depth[tag] -= 1
            if self.depth[self.result[0]] == 0:
                self.started = False
                self.result.append(self.getpos())

    def find_startpos(self, x):
        """Needed to put the start position of the result (self.result[1])
        after the opening tag with the requested id"""
        if self.watch_startpos:
            self.watch_startpos = False
            self.result.append(self.getpos())
    handle_entityref = handle_charref = handle_data = handle_comment = \
    handle_decl = handle_pi = unknown_decl = find_startpos

    def get_result(self):
        if self.result is None:
            return None
        if len(self.result) != 3:
            return None
        lines = self.html.split('\n')
        lines = lines[self.result[1][0]-1:self.result[2][0]]
        lines[0] = lines[0][self.result[1][1]:]
        if len(lines) == 1:
            lines[-1] = lines[-1][:self.result[2][1]-self.result[1][1]]
        lines[-1] = lines[-1][:self.result[2][1]]
        return '\n'.join(lines).strip()
# Hack for https://github.com/rg3/youtube-dl/issues/662
if sys.version_info < (2, 7, 3):
    AttrParser.parse_endtag = (lambda self, i:
        i + len("</scr'+'ipt>")
        if self.rawdata[i:].startswith("</scr'+'ipt>")
        else compat_html_parser.HTMLParser.parse_endtag(self, i))

def get_element_by_id(id, html):
    """Return the content of the tag with the specified ID in the passed HTML document"""
    return get_element_by_attribute("id", id, html)

def get_element_by_attribute(attribute, value, html):
    """Return the content of the tag with the specified attribute in the passed HTML document"""
    parser = AttrParser(attribute, value)
    try:
        parser.loads(html)
    except compat_html_parser.HTMLParseError:
        pass
    return parser.get_result()

class MetaParser(BaseHTMLParser):
    """
    Modified HTMLParser that isolates a meta tag with the specified name 
    attribute.
    """
    def __init__(self, name):
        BaseHTMLParser.__init__(self)
        self.name = name
        self.content = None
        self.result = None

    def handle_starttag(self, tag, attrs):
        if tag != 'meta':
            return
        attrs = dict(attrs)
        if attrs.get('name') == self.name:
            self.result = attrs.get('content')

    def get_result(self):
        return self.result

def get_meta_content(name, html):
    """
    Return the content attribute from the meta tag with the given name attribute.
    """
    parser = MetaParser(name)
    try:
        parser.loads(html)
    except compat_html_parser.HTMLParseError:
        pass
    return parser.get_result()


def clean_html(html):
    """Clean an HTML snippet into a readable string"""
    # Newline vs <br />
    html = html.replace('\n', ' ')
    html = re.sub(r'\s*<\s*br\s*/?\s*>\s*', '\n', html)
    html = re.sub(r'<\s*/\s*p\s*>\s*<\s*p[^>]*>', '\n', html)
    # Strip html tags
    html = re.sub('<.*?>', '', html)
    # Replace html entities
    html = unescapeHTML(html)
    return html.strip()


def sanitize_open(filename, open_mode):
    """Try to open the given filename, and slightly tweak it if this fails.

    Attempts to open the given filename. If this fails, it tries to change
    the filename slightly, step by step, until it's either able to open it
    or it fails and raises a final exception, like the standard open()
    function.

    It returns the tuple (stream, definitive_file_name).
    """
    try:
        if filename == u'-':
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
            return (sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else sys.stdout, filename)
        stream = open(encodeFilename(filename), open_mode)
        return (stream, filename)
    except (IOError, OSError) as err:
        if err.errno in (errno.EACCES,):
            raise

        # In case of error, try to remove win32 forbidden chars
        alt_filename = os.path.join(
                        re.sub(u'[/<>:"\\|\\\\?\\*]', u'#', path_part)
                        for path_part in os.path.split(filename)
                       )
        if alt_filename == filename:
            raise
        else:
            # An exception here should be caught in the caller
            stream = open(encodeFilename(filename), open_mode)
            return (stream, alt_filename)


def timeconvert(timestr):
    """Convert RFC 2822 defined time string into system timestamp"""
    timestamp = None
    timetuple = email.utils.parsedate_tz(timestr)
    if timetuple is not None:
        timestamp = email.utils.mktime_tz(timetuple)
    return timestamp

def sanitize_filename(s, restricted=False, is_id=False):
    """Sanitizes a string so it could be used as part of a filename.
    If restricted is set, use a stricter subset of allowed characters.
    Set is_id if this is not an arbitrary string, but an ID that should be kept if possible
    """
    def replace_insane(char):
        if char == '?' or ord(char) < 32 or ord(char) == 127:
            return ''
        elif char == '"':
            return '' if restricted else '\''
        elif char == ':':
            return '_-' if restricted else ' -'
        elif char in '\\/|*<>':
            return '_'
        if restricted and (char in '!&\'()[]{}$;`^,#' or char.isspace()):
            return '_'
        if restricted and ord(char) > 127:
            return '_'
        return char

    result = u''.join(map(replace_insane, s))
    if not is_id:
        while '__' in result:
            result = result.replace('__', '_')
        result = result.strip('_')
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith('-_'):
            result = result[2:]
        if not result:
            result = '_'
    return result

def orderedSet(iterable):
    """ Remove all duplicates from the input iterable """
    res = []
    for el in iterable:
        if el not in res:
            res.append(el)
    return res

def unescapeHTML(s):
    """
    @param s a string
    """
    assert type(s) == type(u'')

    result = re.sub(u'(?u)&(.+?);', htmlentity_transform, s)
    return result


def encodeFilename(s, for_subprocess=False):
    """
    @param s The name of the file
    """

    assert type(s) == compat_str

    # Python 3 has a Unicode API
    if sys.version_info >= (3, 0):
        return s

    if sys.platform == 'win32' and sys.getwindowsversion()[0] >= 5:
        # Pass u'' directly to use Unicode APIs on Windows 2000 and up
        # (Detecting Windows NT 4 is tricky because 'major >= 4' would
        # match Windows 9x series as well. Besides, NT 4 is obsolete.)
        if not for_subprocess:
            return s
        else:
            # For subprocess calls, encode with locale encoding
            # Refer to http://stackoverflow.com/a/9951851/35070
            encoding = preferredencoding()
    else:
        encoding = sys.getfilesystemencoding()
    if encoding is None:
        encoding = 'utf-8'
    return s.encode(encoding, 'ignore')


def decodeOption(optval):
    if optval is None:
        return optval
    if isinstance(optval, bytes):
        optval = optval.decode(preferredencoding())

    assert isinstance(optval, compat_str)
    return optval

def formatSeconds(secs):
    if secs > 3600:
        return '%d:%02d:%02d' % (secs // 3600, (secs % 3600) // 60, secs % 60)
    elif secs > 60:
        return '%d:%02d' % (secs // 60, secs % 60)
    else:
        return '%d' % secs


def make_HTTPS_handler(opts_no_check_certificate, **kwargs):
    if sys.version_info < (3, 2):
        import httplib

        class HTTPSConnectionV3(httplib.HTTPSConnection):
            def __init__(self, *args, **kwargs):
                httplib.HTTPSConnection.__init__(self, *args, **kwargs)

            def connect(self):
                sock = socket.create_connection((self.host, self.port), self.timeout)
                if getattr(self, '_tunnel_host', False):
                    self.sock = sock
                    self._tunnel()
                try:
                    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
                except ssl.SSLError:
                    self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)

        class HTTPSHandlerV3(compat_urllib_request.HTTPSHandler):
            def https_open(self, req):
                return self.do_open(HTTPSConnectionV3, req)
        return HTTPSHandlerV3(**kwargs)
    else:
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv3)
        context.verify_mode = (ssl.CERT_NONE
                               if opts_no_check_certificate
                               else ssl.CERT_REQUIRED)
        context.set_default_verify_paths()
        try:
            context.load_default_certs()
        except AttributeError:
            pass  # Python < 3.4
        return compat_urllib_request.HTTPSHandler(context=context, **kwargs)

class ExtractorError(Exception):
    """Error during info extraction."""
    def __init__(self, msg, tb=None, expected=False, cause=None):
        """ tb, if given, is the original traceback (so that it can be printed out).
        If expected is set, this is a normal error message and most likely not a bug in youtube-dl.
        """

        if sys.exc_info()[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError):
            expected = True
        if not expected:
            msg = msg + u'; please report this issue on https://yt-dl.org/bug . Be sure to call youtube-dl with the --verbose flag and include its complete output. Make sure you are using the latest version; type  youtube-dl -U  to update.'
        super(ExtractorError, self).__init__(msg)

        self.traceback = tb
        self.exc_info = sys.exc_info()  # preserve original exception
        self.cause = cause

    def format_traceback(self):
        if self.traceback is None:
            return None
        return u''.join(traceback.format_tb(self.traceback))


class RegexNotFoundError(ExtractorError):
    """Error when a regex didn't match"""
    pass


class DownloadError(Exception):
    """Download Error exception.

    This exception may be thrown by FileDownloader objects if they are not
    configured to continue on errors. They will contain the appropriate
    error message.
    """
    def __init__(self, msg, exc_info=None):
        """ exc_info, if given, is the original exception that caused the trouble (as returned by sys.exc_info()). """
        super(DownloadError, self).__init__(msg)
        self.exc_info = exc_info


class SameFileError(Exception):
    """Same File exception.

    This exception will be thrown by FileDownloader objects if they detect
    multiple files would have to be downloaded to the same file on disk.
    """
    pass


class PostProcessingError(Exception):
    """Post Processing exception.

    This exception may be raised by PostProcessor's .run() method to
    indicate an error in the postprocessing task.
    """
    def __init__(self, msg):
        self.msg = msg

class MaxDownloadsReached(Exception):
    """ --max-downloads limit has been reached. """
    pass


class UnavailableVideoError(Exception):
    """Unavailable Format exception.

    This exception will be thrown when a video is requested
    in a format that is not available for that video.
    """
    pass


class ContentTooShortError(Exception):
    """Content Too Short exception.

    This exception may be raised by FileDownloader objects when a file they
    download is too small for what the server announced first, indicating
    the connection was probably interrupted.
    """
    # Both in bytes
    downloaded = None
    expected = None

    def __init__(self, downloaded, expected):
        self.downloaded = downloaded
        self.expected = expected

class YoutubeDLHandler(compat_urllib_request.HTTPHandler):
    """Handler for HTTP requests and responses.

    This class, when installed with an OpenerDirector, automatically adds
    the standard headers to every HTTP request and handles gzipped and
    deflated responses from web servers. If compression is to be avoided in
    a particular request, the original request in the program code only has
    to include the HTTP header "Youtubedl-No-Compression", which will be
    removed before making the real request.

    Part of this code was copied from:

    http://techknack.net/python-urllib2-handlers/

    Andrew Rowls, the author of that code, agreed to release it to the
    public domain.
    """

    @staticmethod
    def deflate(data):
        try:
            return zlib.decompress(data, -zlib.MAX_WBITS)
        except zlib.error:
            return zlib.decompress(data)

    @staticmethod
    def addinfourl_wrapper(stream, headers, url, code):
        if hasattr(compat_urllib_request.addinfourl, 'getcode'):
            return compat_urllib_request.addinfourl(stream, headers, url, code)
        ret = compat_urllib_request.addinfourl(stream, headers, url)
        ret.code = code
        return ret

    def http_request(self, req):
        for h,v in std_headers.items():
            if h in req.headers:
                del req.headers[h]
            req.add_header(h, v)
        if 'Youtubedl-no-compression' in req.headers:
            if 'Accept-encoding' in req.headers:
                del req.headers['Accept-encoding']
            del req.headers['Youtubedl-no-compression']
        if 'Youtubedl-user-agent' in req.headers:
            if 'User-agent' in req.headers:
                del req.headers['User-agent']
            req.headers['User-agent'] = req.headers['Youtubedl-user-agent']
            del req.headers['Youtubedl-user-agent']
        return req

    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get('Content-encoding', '') == 'gzip':
            content = resp.read()
            gz = gzip.GzipFile(fileobj=io.BytesIO(content), mode='rb')
            try:
                uncompressed = io.BytesIO(gz.read())
            except IOError as original_ioerror:
                # There may be junk add the end of the file
                # See http://stackoverflow.com/q/4928560/35070 for details
                for i in range(1, 1024):
                    try:
                        gz = gzip.GzipFile(fileobj=io.BytesIO(content[:-i]), mode='rb')
                        uncompressed = io.BytesIO(gz.read())
                    except IOError:
                        continue
                    break
                else:
                    raise original_ioerror
            resp = self.addinfourl_wrapper(uncompressed, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get('Content-encoding', '') == 'deflate':
            gz = io.BytesIO(self.deflate(resp.read()))
            resp = self.addinfourl_wrapper(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        return resp

    https_request = http_request
    https_response = http_response


def unified_strdate(date_str):
    """Return a string with the date in the format YYYYMMDD"""

    if date_str is None:
        return None

    upload_date = None
    #Replace commas
    date_str = date_str.replace(',', ' ')
    # %z (UTC offset) is only supported in python>=3.2
    date_str = re.sub(r' ?(\+|-)[0-9]{2}:?[0-9]{2}$', '', date_str)
    format_expressions = [
        '%d %B %Y',
        '%d %b %Y',
        '%B %d %Y',
        '%b %d %Y',
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y %H.%M',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f0Z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M',
    ]
    for expression in format_expressions:
        try:
            upload_date = datetime.datetime.strptime(date_str, expression).strftime('%Y%m%d')
        except ValueError:
            pass
    if upload_date is None:
        timetuple = email.utils.parsedate_tz(date_str)
        if timetuple:
            upload_date = datetime.datetime(*timetuple[:6]).strftime('%Y%m%d')
    return upload_date

def determine_ext(url, default_ext=u'unknown_video'):
    guess = url.partition(u'?')[0].rpartition(u'.')[2]
    if re.match(r'^[A-Za-z0-9]+$', guess):
        return guess
    else:
        return default_ext

def subtitles_filename(filename, sub_lang, sub_format):
    return filename.rsplit('.', 1)[0] + u'.' + sub_lang + u'.' + sub_format

def date_from_str(date_str):
    """
    Return a datetime object from a string in the format YYYYMMDD or
    (now|today)[+-][0-9](day|week|month|year)(s)?"""
    today = datetime.date.today()
    if date_str == 'now'or date_str == 'today':
        return today
    match = re.match('(now|today)(?P<sign>[+-])(?P<time>\d+)(?P<unit>day|week|month|year)(s)?', date_str)
    if match is not None:
        sign = match.group('sign')
        time = int(match.group('time'))
        if sign == '-':
            time = -time
        unit = match.group('unit')
        #A bad aproximation?
        if unit == 'month':
            unit = 'day'
            time *= 30
        elif unit == 'year':
            unit = 'day'
            time *= 365
        unit += 's'
        delta = datetime.timedelta(**{unit: time})
        return today + delta
    return datetime.datetime.strptime(date_str, "%Y%m%d").date()
    
def hyphenate_date(date_str):
    """
    Convert a date in 'YYYYMMDD' format to 'YYYY-MM-DD' format"""
    match = re.match(r'^(\d\d\d\d)(\d\d)(\d\d)$', date_str)
    if match is not None:
        return '-'.join(match.groups())
    else:
        return date_str

class DateRange(object):
    """Represents a time interval between two dates"""
    def __init__(self, start=None, end=None):
        """start and end must be strings in the format accepted by date"""
        if start is not None:
            self.start = date_from_str(start)
        else:
            self.start = datetime.datetime.min.date()
        if end is not None:
            self.end = date_from_str(end)
        else:
            self.end = datetime.datetime.max.date()
        if self.start > self.end:
            raise ValueError('Date range: "%s" , the start date must be before the end date' % self)
    @classmethod
    def day(cls, day):
        """Returns a range that only contains the given day"""
        return cls(day,day)
    def __contains__(self, date):
        """Check if the date is in the range"""
        if not isinstance(date, datetime.date):
            date = date_from_str(date)
        return self.start <= date <= self.end
    def __str__(self):
        return '%s - %s' % ( self.start.isoformat(), self.end.isoformat())


def platform_name():
    """ Returns the platform name as a compat_str """
    res = platform.platform()
    if isinstance(res, bytes):
        res = res.decode(preferredencoding())

    assert isinstance(res, compat_str)
    return res


def write_string(s, out=None):
    if out is None:
        out = sys.stderr
    assert type(s) == compat_str

    if ('b' in getattr(out, 'mode', '') or
            sys.version_info[0] < 3):  # Python 2 lies about mode of sys.stderr
        s = s.encode(preferredencoding(), 'ignore')
    try:
        out.write(s)
    except UnicodeEncodeError:
        # In Windows shells, this can fail even when the codec is just charmap!?
        # See https://wiki.python.org/moin/PrintFails#Issue
        if sys.platform == 'win32' and hasattr(out, 'encoding'):
            s = s.encode(out.encoding, 'ignore').decode(out.encoding)
            out.write(s)
        else:
            raise

    out.flush()


def bytes_to_intlist(bs):
    if not bs:
        return []
    if isinstance(bs[0], int):  # Python 3
        return list(bs)
    else:
        return [ord(c) for c in bs]


def intlist_to_bytes(xs):
    if not xs:
        return b''
    if isinstance(chr(0), bytes):  # Python 2
        return ''.join([chr(x) for x in xs])
    else:
        return bytes(xs)


def get_cachedir(params={}):
    cache_root = os.environ.get('XDG_CACHE_HOME',
                                os.path.expanduser('~/.cache'))
    return params.get('cachedir', os.path.join(cache_root, 'youtube-dl'))


# Cross-platform file locking
if sys.platform == 'win32':
    import ctypes.wintypes
    import msvcrt

    class OVERLAPPED(ctypes.Structure):
        _fields_ = [
            ('Internal', ctypes.wintypes.LPVOID),
            ('InternalHigh', ctypes.wintypes.LPVOID),
            ('Offset', ctypes.wintypes.DWORD),
            ('OffsetHigh', ctypes.wintypes.DWORD),
            ('hEvent', ctypes.wintypes.HANDLE),
        ]

    kernel32 = ctypes.windll.kernel32
    LockFileEx = kernel32.LockFileEx
    LockFileEx.argtypes = [
        ctypes.wintypes.HANDLE,     # hFile
        ctypes.wintypes.DWORD,      # dwFlags
        ctypes.wintypes.DWORD,      # dwReserved
        ctypes.wintypes.DWORD,      # nNumberOfBytesToLockLow
        ctypes.wintypes.DWORD,      # nNumberOfBytesToLockHigh
        ctypes.POINTER(OVERLAPPED)  # Overlapped
    ]
    LockFileEx.restype = ctypes.wintypes.BOOL
    UnlockFileEx = kernel32.UnlockFileEx
    UnlockFileEx.argtypes = [
        ctypes.wintypes.HANDLE,     # hFile
        ctypes.wintypes.DWORD,      # dwReserved
        ctypes.wintypes.DWORD,      # nNumberOfBytesToLockLow
        ctypes.wintypes.DWORD,      # nNumberOfBytesToLockHigh
        ctypes.POINTER(OVERLAPPED)  # Overlapped
    ]
    UnlockFileEx.restype = ctypes.wintypes.BOOL
    whole_low = 0xffffffff
    whole_high = 0x7fffffff

    def _lock_file(f, exclusive):
        overlapped = OVERLAPPED()
        overlapped.Offset = 0
        overlapped.OffsetHigh = 0
        overlapped.hEvent = 0
        f._lock_file_overlapped_p = ctypes.pointer(overlapped)
        handle = msvcrt.get_osfhandle(f.fileno())
        if not LockFileEx(handle, 0x2 if exclusive else 0x0, 0,
                          whole_low, whole_high, f._lock_file_overlapped_p):
            raise OSError('Locking file failed: %r' % ctypes.FormatError())

    def _unlock_file(f):
        assert f._lock_file_overlapped_p
        handle = msvcrt.get_osfhandle(f.fileno())
        if not UnlockFileEx(handle, 0,
                            whole_low, whole_high, f._lock_file_overlapped_p):
            raise OSError('Unlocking file failed: %r' % ctypes.FormatError())

else:
    import fcntl

    def _lock_file(f, exclusive):
        fcntl.lockf(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)

    def _unlock_file(f):
        fcntl.lockf(f, fcntl.LOCK_UN)


class locked_file(object):
    def __init__(self, filename, mode, encoding=None):
        assert mode in ['r', 'a', 'w']
        self.f = io.open(filename, mode, encoding=encoding)
        self.mode = mode

    def __enter__(self):
        exclusive = self.mode != 'r'
        try:
            _lock_file(self.f, exclusive)
        except IOError:
            self.f.close()
            raise
        return self

    def __exit__(self, etype, value, traceback):
        try:
            _unlock_file(self.f)
        finally:
            self.f.close()

    def __iter__(self):
        return iter(self.f)

    def write(self, *args):
        return self.f.write(*args)

    def read(self, *args):
        return self.f.read(*args)


def shell_quote(args):
    quoted_args = []
    encoding = sys.getfilesystemencoding()
    if encoding is None:
        encoding = 'utf-8'
    for a in args:
        if isinstance(a, bytes):
            # We may get a filename encoded with 'encodeFilename'
            a = a.decode(encoding)
        quoted_args.append(pipes.quote(a))
    return u' '.join(quoted_args)


def takewhile_inclusive(pred, seq):
    """ Like itertools.takewhile, but include the latest evaluated element
        (the first element so that Not pred(e)) """
    for e in seq:
        yield e
        if not pred(e):
            return


def smuggle_url(url, data):
    """ Pass additional data in a URL for internal use. """

    sdata = compat_urllib_parse.urlencode(
        {u'__youtubedl_smuggle': json.dumps(data)})
    return url + u'#' + sdata


def unsmuggle_url(smug_url, default=None):
    if not '#__youtubedl_smuggle' in smug_url:
        return smug_url, default
    url, _, sdata = smug_url.rpartition(u'#')
    jsond = compat_parse_qs(sdata)[u'__youtubedl_smuggle'][0]
    data = json.loads(jsond)
    return url, data


def format_bytes(bytes):
    if bytes is None:
        return u'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = [u'B', u'KiB', u'MiB', u'GiB', u'TiB', u'PiB', u'EiB', u'ZiB', u'YiB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return u'%.2f%s' % (converted, suffix)


def str_to_int(int_str):
    int_str = re.sub(r'[,\.]', u'', int_str)
    return int(int_str)


def get_term_width():
    columns = os.environ.get('COLUMNS', None)
    if columns:
        return int(columns)

    try:
        sp = subprocess.Popen(
            ['stty', 'size'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = sp.communicate()
        return int(out.split()[1])
    except:
        pass
    return None


def month_by_name(name):
    """ Return the number of a month by (locale-independently) English name """

    ENGLISH_NAMES = [
        u'January', u'February', u'March', u'April', u'May', u'June',
        u'July', u'August', u'September', u'October', u'November', u'December']
    try:
        return ENGLISH_NAMES.index(name) + 1
    except ValueError:
        return None


def fix_xml_ampersands(xml_str):
    """Replace all the '&' by '&amp;' in XML"""
    return re.sub(
        r'&(?!amp;|lt;|gt;|apos;|quot;|#x[0-9a-fA-F]{,4};|#[0-9]{,4};)',
        u'&amp;',
        xml_str)


def setproctitle(title):
    assert isinstance(title, compat_str)
    try:
        libc = ctypes.cdll.LoadLibrary("libc.so.6")
    except OSError:
        return
    title = title
    buf = ctypes.create_string_buffer(len(title) + 1)
    buf.value = title.encode('utf-8')
    try:
        libc.prctl(15, ctypes.byref(buf), 0, 0, 0)
    except AttributeError:
        return  # Strange libc, just skip this


def remove_start(s, start):
    if s.startswith(start):
        return s[len(start):]
    return s


def url_basename(url):
    path = compat_urlparse.urlparse(url).path
    return path.strip(u'/').split(u'/')[-1]


class HEADRequest(compat_urllib_request.Request):
    def get_method(self):
        return "HEAD"


def int_or_none(v, scale=1):
    return v if v is None else (int(v) // scale)


def parse_duration(s):
    if s is None:
        return None

    m = re.match(
        r'(?:(?:(?P<hours>[0-9]+)[:h])?(?P<mins>[0-9]+)[:m])?(?P<secs>[0-9]+)s?$', s)
    if not m:
        return None
    res = int(m.group('secs'))
    if m.group('mins'):
        res += int(m.group('mins')) * 60
        if m.group('hours'):
            res += int(m.group('hours')) * 60 * 60
    return res


def prepend_extension(filename, ext):
    name, real_ext = os.path.splitext(filename) 
    return u'{0}.{1}{2}'.format(name, ext, real_ext)


def check_executable(exe, args=[]):
    """ Checks if the given binary is installed somewhere in PATH, and returns its name.
    args can be a list of arguments for a short output (like -version) """
    try:
        subprocess.Popen([exe] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except OSError:
        return False
    return exe


class PagedList(object):
    def __init__(self, pagefunc, pagesize):
        self._pagefunc = pagefunc
        self._pagesize = pagesize

    def __len__(self):
        # This is only useful for tests
        return len(self.getslice())

    def getslice(self, start=0, end=None):
        res = []
        for pagenum in itertools.count(start // self._pagesize):
            firstid = pagenum * self._pagesize
            nextfirstid = pagenum * self._pagesize + self._pagesize
            if start >= nextfirstid:
                continue

            page_results = list(self._pagefunc(pagenum))

            startv = (
                start % self._pagesize
                if firstid <= start < nextfirstid
                else 0)

            endv = (
                ((end - 1) % self._pagesize) + 1
                if (end is not None and firstid <= end <= nextfirstid)
                else None)

            if startv != 0 or endv is not None:
                page_results = page_results[startv:endv]
            res.extend(page_results)

            # A little optimization - if current page is not "full", ie. does
            # not contain page_size videos then we can assume that this page
            # is the last one - there are no more ids on further pages -
            # i.e. no need to query again.
            if len(page_results) + startv < self._pagesize:
                break

            # If we got the whole page, but the next page is not interesting,
            # break out early as well
            if end == nextfirstid:
                break
        return res


def uppercase_escape(s):
    return re.sub(
        r'\\U([0-9a-fA-F]{8})',
        lambda m: compat_chr(int(m.group(1), base=16)), s)

try:
    struct.pack(u'!I', 0)
except TypeError:
    # In Python 2.6 (and some 2.7 versions), struct requires a bytes argument
    def struct_pack(spec, *args):
        if isinstance(spec, compat_str):
            spec = spec.encode('ascii')
        return struct.pack(spec, *args)

    def struct_unpack(spec, *args):
        if isinstance(spec, compat_str):
            spec = spec.encode('ascii')
        return struct.unpack(spec, *args)
else:
    struct_pack = struct.pack
    struct_unpack = struct.unpack


def read_batch_urls(batch_fd):
    def fixup(url):
        if not isinstance(url, compat_str):
            url = url.decode('utf-8', 'replace')
        BOM_UTF8 = u'\xef\xbb\xbf'
        if url.startswith(BOM_UTF8):
            url = url[len(BOM_UTF8):]
        url = url.strip()
        if url.startswith(('#', ';', ']')):
            return False
        return url

    with contextlib.closing(batch_fd) as fd:
        return [url for url in map(fixup, fd) if url]


def urlencode_postdata(*args, **kargs):
    return compat_urllib_parse.urlencode(*args, **kargs).encode('ascii')


def parse_xml(s):
    class TreeBuilder(xml.etree.ElementTree.TreeBuilder):
        def doctype(self, name, pubid, system):
            pass  # Ignore doctypes

    parser = xml.etree.ElementTree.XMLParser(target=TreeBuilder())
    kwargs = {'parser': parser} if sys.version_info >= (2, 7) else {}
    return xml.etree.ElementTree.XML(s.encode('utf-8'), **kwargs)


if sys.version_info < (3, 0) and sys.platform == 'win32':
    def compat_getpass(prompt, *args, **kwargs):
        if isinstance(prompt, compat_str):
            prompt = prompt.encode(preferredencoding())
        return getpass.getpass(prompt, *args, **kwargs)
else:
    compat_getpass = getpass.getpass


US_RATINGS = {
    'G': 0,
    'PG': 10,
    'PG-13': 13,
    'R': 16,
    'NC': 18,
}
