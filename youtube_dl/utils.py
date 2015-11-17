#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import calendar
import codecs
import contextlib
import ctypes
import datetime
import email.utils
import errno
import functools
import gzip
import itertools
import io
import json
import locale
import math
import operator
import os
import pipes
import platform
import re
import ssl
import socket
import struct
import subprocess
import sys
import tempfile
import traceback
import xml.etree.ElementTree
import zlib

from .compat import (
    compat_basestring,
    compat_chr,
    compat_etree_fromstring,
    compat_html_entities,
    compat_http_client,
    compat_kwargs,
    compat_parse_qs,
    compat_socket_create_connection,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse,
    compat_urllib_parse_urlparse,
    compat_urllib_request,
    compat_urlparse,
    shlex_quote,
)


# This is not clearly defined otherwise
compiled_regex_type = type(re.compile(''))

std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20150101 Firefox/20.0 (Chrome)',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-us,en;q=0.5',
}


NO_DEFAULT = object()

ENGLISH_MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']


def preferredencoding():
    """Get preferred encoding.

    Returns the best encoding scheme for the system, based on
    locale.getpreferredencoding() and some further tweaks.
    """
    try:
        pref = locale.getpreferredencoding()
        'TEST'.encode(pref)
    except Exception:
        pref = 'UTF-8'

    return pref


def write_json_file(obj, fn):
    """ Encode obj as JSON and write it to fn, atomically if possible """

    fn = encodeFilename(fn)
    if sys.version_info < (3, 0) and sys.platform != 'win32':
        encoding = get_filesystem_encoding()
        # os.path.basename returns a bytes object, but NamedTemporaryFile
        # will fail if the filename contains non ascii characters unless we
        # use a unicode object
        path_basename = lambda f: os.path.basename(fn).decode(encoding)
        # the same for os.path.dirname
        path_dirname = lambda f: os.path.dirname(fn).decode(encoding)
    else:
        path_basename = os.path.basename
        path_dirname = os.path.dirname

    args = {
        'suffix': '.tmp',
        'prefix': path_basename(fn) + '.',
        'dir': path_dirname(fn),
        'delete': False,
    }

    # In Python 2.x, json.dump expects a bytestream.
    # In Python 3.x, it writes to a character stream
    if sys.version_info < (3, 0):
        args['mode'] = 'wb'
    else:
        args.update({
            'mode': 'w',
            'encoding': 'utf-8',
        })

    tf = tempfile.NamedTemporaryFile(**compat_kwargs(args))

    try:
        with tf:
            json.dump(obj, tf)
        if sys.platform == 'win32':
            # Need to remove existing file on Windows, else os.rename raises
            # WindowsError or FileExistsError.
            try:
                os.unlink(fn)
            except OSError:
                pass
        os.rename(tf.name, fn)
    except Exception:
        try:
            os.remove(tf.name)
        except OSError:
            pass
        raise


if sys.version_info >= (2, 7):
    def find_xpath_attr(node, xpath, key, val=None):
        """ Find the xpath xpath[@key=val] """
        assert re.match(r'^[a-zA-Z_-]+$', key)
        if val:
            assert re.match(r'^[a-zA-Z0-9@\s:._-]*$', val)
        expr = xpath + ('[@%s]' % key if val is None else "[@%s='%s']" % (key, val))
        return node.find(expr)
else:
    def find_xpath_attr(node, xpath, key, val=None):
        # Here comes the crazy part: In 2.6, if the xpath is a unicode,
        # .//node does not match if a node is a direct child of . !
        if isinstance(xpath, compat_str):
            xpath = xpath.encode('ascii')

        for f in node.findall(xpath):
            if key not in f.attrib:
                continue
            if val is None or f.attrib.get(key) == val:
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


def xpath_element(node, xpath, name=None, fatal=False, default=NO_DEFAULT):
    def _find_xpath(xpath):
        if sys.version_info < (2, 7):  # Crazy 2.6
            xpath = xpath.encode('ascii')
        return node.find(xpath)

    if isinstance(xpath, (str, compat_str)):
        n = _find_xpath(xpath)
    else:
        for xp in xpath:
            n = _find_xpath(xp)
            if n is not None:
                break

    if n is None:
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            name = xpath if name is None else name
            raise ExtractorError('Could not find XML element %s' % name)
        else:
            return None
    return n


def xpath_text(node, xpath, name=None, fatal=False, default=NO_DEFAULT):
    n = xpath_element(node, xpath, name, fatal=fatal, default=default)
    if n is None or n == default:
        return n
    if n.text is None:
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            name = xpath if name is None else name
            raise ExtractorError('Could not find XML element\'s text %s' % name)
        else:
            return None
    return n.text


def xpath_attr(node, xpath, key, name=None, fatal=False, default=NO_DEFAULT):
    n = find_xpath_attr(node, xpath, key)
    if n is None:
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            name = '%s[@%s]' % (xpath, key) if name is None else name
            raise ExtractorError('Could not find XML attribute %s' % name)
        else:
            return None
    return n.attrib[key]


def get_element_by_id(id, html):
    """Return the content of the tag with the specified ID in the passed HTML document"""
    return get_element_by_attribute("id", id, html)


def get_element_by_attribute(attribute, value, html):
    """Return the content of the tag with the specified attribute in the passed HTML document"""

    m = re.search(r'''(?xs)
        <([a-zA-Z0-9:._-]+)
         (?:\s+[a-zA-Z0-9:._-]+(?:=[a-zA-Z0-9:._-]+|="[^"]+"|='[^']+'))*?
         \s+%s=['"]?%s['"]?
         (?:\s+[a-zA-Z0-9:._-]+(?:=[a-zA-Z0-9:._-]+|="[^"]+"|='[^']+'))*?
        \s*>
        (?P<content>.*?)
        </\1>
    ''' % (re.escape(attribute), re.escape(value)), html)

    if not m:
        return None
    res = m.group('content')

    if res.startswith('"') or res.startswith("'"):
        res = res[1:-1]

    return unescapeHTML(res)


def clean_html(html):
    """Clean an HTML snippet into a readable string"""

    if html is None:  # Convenience for sanitizing descriptions etc.
        return html

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
        if filename == '-':
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
        alt_filename = sanitize_path(filename)
        if alt_filename == filename:
            raise
        else:
            # An exception here should be caught in the caller
            stream = open(encodeFilename(alt_filename), open_mode)
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

    # Handle timestamps
    s = re.sub(r'[0-9]+(?::[0-9]+)+', lambda m: m.group(0).replace(':', '_'), s)
    result = ''.join(map(replace_insane, s))
    if not is_id:
        while '__' in result:
            result = result.replace('__', '_')
        result = result.strip('_')
        # Common case of "Foreign band name - English song title"
        if restricted and result.startswith('-_'):
            result = result[2:]
        if result.startswith('-'):
            result = '_' + result[len('-'):]
        result = result.lstrip('.')
        if not result:
            result = '_'
    return result


def sanitize_path(s):
    """Sanitizes and normalizes path on Windows"""
    if sys.platform != 'win32':
        return s
    drive_or_unc, _ = os.path.splitdrive(s)
    if sys.version_info < (2, 7) and not drive_or_unc:
        drive_or_unc, _ = os.path.splitunc(s)
    norm_path = os.path.normpath(remove_start(s, drive_or_unc)).split(os.path.sep)
    if drive_or_unc:
        norm_path.pop(0)
    sanitized_path = [
        path_part if path_part in ['.', '..'] else re.sub('(?:[/<>:"\\|\\\\?\\*]|[\s.]$)', '#', path_part)
        for path_part in norm_path]
    if drive_or_unc:
        sanitized_path.insert(0, drive_or_unc + os.path.sep)
    return os.path.join(*sanitized_path)


def orderedSet(iterable):
    """ Remove all duplicates from the input iterable """
    res = []
    for el in iterable:
        if el not in res:
            res.append(el)
    return res


def _htmlentity_transform(entity):
    """Transforms an HTML entity to a character."""
    # Known non-numeric HTML entity
    if entity in compat_html_entities.name2codepoint:
        return compat_chr(compat_html_entities.name2codepoint[entity])

    mobj = re.match(r'#(x[0-9a-fA-F]+|[0-9]+)', entity)
    if mobj is not None:
        numstr = mobj.group(1)
        if numstr.startswith('x'):
            base = 16
            numstr = '0%s' % numstr
        else:
            base = 10
        # See https://github.com/rg3/youtube-dl/issues/7518
        try:
            return compat_chr(int(numstr, base))
        except ValueError:
            pass

    # Unknown entity in name, return its literal representation
    return '&%s;' % entity


def unescapeHTML(s):
    if s is None:
        return None
    assert type(s) == compat_str

    return re.sub(
        r'&([^;]+);', lambda m: _htmlentity_transform(m.group(1)), s)


def get_subprocess_encoding():
    if sys.platform == 'win32' and sys.getwindowsversion()[0] >= 5:
        # For subprocess calls, encode with locale encoding
        # Refer to http://stackoverflow.com/a/9951851/35070
        encoding = preferredencoding()
    else:
        encoding = sys.getfilesystemencoding()
    if encoding is None:
        encoding = 'utf-8'
    return encoding


def encodeFilename(s, for_subprocess=False):
    """
    @param s The name of the file
    """

    assert type(s) == compat_str

    # Python 3 has a Unicode API
    if sys.version_info >= (3, 0):
        return s

    # Pass '' directly to use Unicode APIs on Windows 2000 and up
    # (Detecting Windows NT 4 is tricky because 'major >= 4' would
    # match Windows 9x series as well. Besides, NT 4 is obsolete.)
    if not for_subprocess and sys.platform == 'win32' and sys.getwindowsversion()[0] >= 5:
        return s

    return s.encode(get_subprocess_encoding(), 'ignore')


def decodeFilename(b, for_subprocess=False):

    if sys.version_info >= (3, 0):
        return b

    if not isinstance(b, bytes):
        return b

    return b.decode(get_subprocess_encoding(), 'ignore')


def encodeArgument(s):
    if not isinstance(s, compat_str):
        # Legacy code that uses byte strings
        # Uncomment the following line after fixing all post processors
        # assert False, 'Internal error: %r should be of type %r, is %r' % (s, compat_str, type(s))
        s = s.decode('ascii')
    return encodeFilename(s, True)


def decodeArgument(b):
    return decodeFilename(b, True)


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


def make_HTTPS_handler(params, **kwargs):
    opts_no_check_certificate = params.get('nocheckcertificate', False)
    if hasattr(ssl, 'create_default_context'):  # Python >= 3.4 or 2.7.9
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if opts_no_check_certificate:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        try:
            return YoutubeDLHTTPSHandler(params, context=context, **kwargs)
        except TypeError:
            # Python 2.7.8
            # (create_default_context present but HTTPSHandler has no context=)
            pass

    if sys.version_info < (3, 2):
        return YoutubeDLHTTPSHandler(params, **kwargs)
    else:  # Python < 3.4
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.verify_mode = (ssl.CERT_NONE
                               if opts_no_check_certificate
                               else ssl.CERT_REQUIRED)
        context.set_default_verify_paths()
        return YoutubeDLHTTPSHandler(params, context=context, **kwargs)


def bug_reports_message():
    if ytdl_is_updateable():
        update_cmd = 'type  youtube-dl -U  to update'
    else:
        update_cmd = 'see  https://yt-dl.org/update  on how to update'
    msg = '; please report this issue on https://yt-dl.org/bug .'
    msg += ' Make sure you are using the latest version; %s.' % update_cmd
    msg += ' Be sure to call youtube-dl with the --verbose flag and include its complete output.'
    return msg


class ExtractorError(Exception):
    """Error during info extraction."""

    def __init__(self, msg, tb=None, expected=False, cause=None, video_id=None):
        """ tb, if given, is the original traceback (so that it can be printed out).
        If expected is set, this is a normal error message and most likely not a bug in youtube-dl.
        """

        if sys.exc_info()[0] in (compat_urllib_error.URLError, socket.timeout, UnavailableVideoError):
            expected = True
        if video_id is not None:
            msg = video_id + ': ' + msg
        if cause:
            msg += ' (caused by %r)' % cause
        if not expected:
            msg += bug_reports_message()
        super(ExtractorError, self).__init__(msg)

        self.traceback = tb
        self.exc_info = sys.exc_info()  # preserve original exception
        self.cause = cause
        self.video_id = video_id

    def format_traceback(self):
        if self.traceback is None:
            return None
        return ''.join(traceback.format_tb(self.traceback))


class UnsupportedError(ExtractorError):
    def __init__(self, url):
        super(UnsupportedError, self).__init__(
            'Unsupported URL: %s' % url, expected=True)
        self.url = url


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

    def __init__(self, downloaded, expected):
        # Both in bytes
        self.downloaded = downloaded
        self.expected = expected


def _create_http_connection(ydl_handler, http_class, is_https, *args, **kwargs):
    # Working around python 2 bug (see http://bugs.python.org/issue17849) by limiting
    # expected HTTP responses to meet HTTP/1.0 or later (see also
    # https://github.com/rg3/youtube-dl/issues/6727)
    if sys.version_info < (3, 0):
        kwargs[b'strict'] = True
    hc = http_class(*args, **kwargs)
    source_address = ydl_handler._params.get('source_address')
    if source_address is not None:
        sa = (source_address, 0)
        if hasattr(hc, 'source_address'):  # Python 2.7+
            hc.source_address = sa
        else:  # Python 2.6
            def _hc_connect(self, *args, **kwargs):
                sock = compat_socket_create_connection(
                    (self.host, self.port), self.timeout, sa)
                if is_https:
                    self.sock = ssl.wrap_socket(
                        sock, self.key_file, self.cert_file,
                        ssl_version=ssl.PROTOCOL_TLSv1)
                else:
                    self.sock = sock
            hc.connect = functools.partial(_hc_connect, hc)

    return hc


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

    def __init__(self, params, *args, **kwargs):
        compat_urllib_request.HTTPHandler.__init__(self, *args, **kwargs)
        self._params = params

    def http_open(self, req):
        return self.do_open(functools.partial(
            _create_http_connection, self, compat_http_client.HTTPConnection, False),
            req)

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
        # According to RFC 3986, URLs can not contain non-ASCII characters, however this is not
        # always respected by websites, some tend to give out URLs with non percent-encoded
        # non-ASCII characters (see telemb.py, ard.py [#3412])
        # urllib chokes on URLs with non-ASCII characters (see http://bugs.python.org/issue3991)
        # To work around aforementioned issue we will replace request's original URL with
        # percent-encoded one
        # Since redirects are also affected (e.g. http://www.southpark.de/alle-episoden/s18e09)
        # the code of this workaround has been moved here from YoutubeDL.urlopen()
        url = req.get_full_url()
        url_escaped = escape_url(url)

        # Substitute URL if any change after escaping
        if url != url_escaped:
            req_type = HEADRequest if req.get_method() == 'HEAD' else compat_urllib_request.Request
            new_req = req_type(
                url_escaped, data=req.data, headers=req.headers,
                origin_req_host=req.origin_req_host, unverifiable=req.unverifiable)
            new_req.timeout = req.timeout
            req = new_req

        for h, v in std_headers.items():
            # Capitalize is needed because of Python bug 2275: http://bugs.python.org/issue2275
            # The dict keys are capitalized because of this bug by urllib
            if h.capitalize() not in req.headers:
                req.add_header(h, v)
        if 'Youtubedl-no-compression' in req.headers:
            if 'Accept-encoding' in req.headers:
                del req.headers['Accept-encoding']
            del req.headers['Youtubedl-no-compression']

        if sys.version_info < (2, 7) and '#' in req.get_full_url():
            # Python 2.6 is brain-dead when it comes to fragments
            req._Request__original = req._Request__original.partition('#')[0]
            req._Request__r_type = req._Request__r_type.partition('#')[0]

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
        # Percent-encode redirect URL of Location HTTP header to satisfy RFC 3986 (see
        # https://github.com/rg3/youtube-dl/issues/6457).
        if 300 <= resp.code < 400:
            location = resp.headers.get('Location')
            if location:
                # As of RFC 2616 default charset is iso-8859-1 that is respected by python 3
                if sys.version_info >= (3, 0):
                    location = location.encode('iso-8859-1').decode('utf-8')
                location_escaped = escape_url(location)
                if location != location_escaped:
                    del resp.headers['Location']
                    resp.headers['Location'] = location_escaped
        return resp

    https_request = http_request
    https_response = http_response


class YoutubeDLHTTPSHandler(compat_urllib_request.HTTPSHandler):
    def __init__(self, params, https_conn_class=None, *args, **kwargs):
        compat_urllib_request.HTTPSHandler.__init__(self, *args, **kwargs)
        self._https_conn_class = https_conn_class or compat_http_client.HTTPSConnection
        self._params = params

    def https_open(self, req):
        kwargs = {}
        if hasattr(self, '_context'):  # python > 2.6
            kwargs['context'] = self._context
        if hasattr(self, '_check_hostname'):  # python 3.x
            kwargs['check_hostname'] = self._check_hostname
        return self.do_open(functools.partial(
            _create_http_connection, self, self._https_conn_class, True),
            req, **kwargs)


class YoutubeDLCookieProcessor(compat_urllib_request.HTTPCookieProcessor):
    def __init__(self, cookiejar=None):
        compat_urllib_request.HTTPCookieProcessor.__init__(self, cookiejar)

    def http_response(self, request, response):
        # Python 2 will choke on next HTTP request in row if there are non-ASCII
        # characters in Set-Cookie HTTP header of last response (see
        # https://github.com/rg3/youtube-dl/issues/6769).
        # In order to at least prevent crashing we will percent encode Set-Cookie
        # header before HTTPCookieProcessor starts processing it.
        # if sys.version_info < (3, 0) and response.headers:
        #     for set_cookie_header in ('Set-Cookie', 'Set-Cookie2'):
        #         set_cookie = response.headers.get(set_cookie_header)
        #         if set_cookie:
        #             set_cookie_escaped = compat_urllib_parse.quote(set_cookie, b"%/;:@&=+$,!~*'()?#[] ")
        #             if set_cookie != set_cookie_escaped:
        #                 del response.headers[set_cookie_header]
        #                 response.headers[set_cookie_header] = set_cookie_escaped
        return compat_urllib_request.HTTPCookieProcessor.http_response(self, request, response)

    https_request = compat_urllib_request.HTTPCookieProcessor.http_request
    https_response = http_response


def parse_iso8601(date_str, delimiter='T', timezone=None):
    """ Return a UNIX timestamp from the given date """

    if date_str is None:
        return None

    date_str = re.sub(r'\.[0-9]+', '', date_str)

    if timezone is None:
        m = re.search(
            r'(?:Z$| ?(?P<sign>\+|-)(?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})$)',
            date_str)
        if not m:
            timezone = datetime.timedelta()
        else:
            date_str = date_str[:-len(m.group(0))]
            if not m.group('sign'):
                timezone = datetime.timedelta()
            else:
                sign = 1 if m.group('sign') == '+' else -1
                timezone = datetime.timedelta(
                    hours=sign * int(m.group('hours')),
                    minutes=sign * int(m.group('minutes')))
    try:
        date_format = '%Y-%m-%d{0}%H:%M:%S'.format(delimiter)
        dt = datetime.datetime.strptime(date_str, date_format) - timezone
        return calendar.timegm(dt.timetuple())
    except ValueError:
        pass


def unified_strdate(date_str, day_first=True):
    """Return a string with the date in the format YYYYMMDD"""

    if date_str is None:
        return None
    upload_date = None
    # Replace commas
    date_str = date_str.replace(',', ' ')
    # %z (UTC offset) is only supported in python>=3.2
    if not re.match(r'^[0-9]{1,2}-[0-9]{1,2}-[0-9]{4}$', date_str):
        date_str = re.sub(r' ?(\+|-)[0-9]{2}:?[0-9]{2}$', '', date_str)
    # Remove AM/PM + timezone
    date_str = re.sub(r'(?i)\s*(?:AM|PM)(?:\s+[A-Z]+)?', '', date_str)

    format_expressions = [
        '%d %B %Y',
        '%d %b %Y',
        '%B %d %Y',
        '%b %d %Y',
        '%b %dst %Y %I:%M%p',
        '%b %dnd %Y %I:%M%p',
        '%b %dth %Y %I:%M%p',
        '%Y %m %d',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%d.%m.%Y %H:%M',
        '%d.%m.%Y %H.%M',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S.%f0Z',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M',
    ]
    if day_first:
        format_expressions.extend([
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%d/%m/%y',
            '%d/%m/%Y %H:%M:%S',
        ])
    else:
        format_expressions.extend([
            '%m-%d-%Y',
            '%m.%d.%Y',
            '%m/%d/%Y',
            '%m/%d/%y',
            '%m/%d/%Y %H:%M:%S',
        ])
    for expression in format_expressions:
        try:
            upload_date = datetime.datetime.strptime(date_str, expression).strftime('%Y%m%d')
        except ValueError:
            pass
    if upload_date is None:
        timetuple = email.utils.parsedate_tz(date_str)
        if timetuple:
            upload_date = datetime.datetime(*timetuple[:6]).strftime('%Y%m%d')
    if upload_date is not None:
        return compat_str(upload_date)


def determine_ext(url, default_ext='unknown_video'):
    if url is None:
        return default_ext
    guess = url.partition('?')[0].rpartition('.')[2]
    if re.match(r'^[A-Za-z0-9]+$', guess):
        return guess
    else:
        return default_ext


def subtitles_filename(filename, sub_lang, sub_format):
    return filename.rsplit('.', 1)[0] + '.' + sub_lang + '.' + sub_format


def date_from_str(date_str):
    """
    Return a datetime object from a string in the format YYYYMMDD or
    (now|today)[+-][0-9](day|week|month|year)(s)?"""
    today = datetime.date.today()
    if date_str in ('now', 'today'):
        return today
    if date_str == 'yesterday':
        return today - datetime.timedelta(days=1)
    match = re.match('(now|today)(?P<sign>[+-])(?P<time>\d+)(?P<unit>day|week|month|year)(s)?', date_str)
    if match is not None:
        sign = match.group('sign')
        time = int(match.group('time'))
        if sign == '-':
            time = -time
        unit = match.group('unit')
        # A bad aproximation?
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
        return cls(day, day)

    def __contains__(self, date):
        """Check if the date is in the range"""
        if not isinstance(date, datetime.date):
            date = date_from_str(date)
        return self.start <= date <= self.end

    def __str__(self):
        return '%s - %s' % (self.start.isoformat(), self.end.isoformat())


def platform_name():
    """ Returns the platform name as a compat_str """
    res = platform.platform()
    if isinstance(res, bytes):
        res = res.decode(preferredencoding())

    assert isinstance(res, compat_str)
    return res


def _windows_write_string(s, out):
    """ Returns True if the string was written using special methods,
    False if it has yet to be written out."""
    # Adapted from http://stackoverflow.com/a/3259271/35070

    import ctypes
    import ctypes.wintypes

    WIN_OUTPUT_IDS = {
        1: -11,
        2: -12,
    }

    try:
        fileno = out.fileno()
    except AttributeError:
        # If the output stream doesn't have a fileno, it's virtual
        return False
    except io.UnsupportedOperation:
        # Some strange Windows pseudo files?
        return False
    if fileno not in WIN_OUTPUT_IDS:
        return False

    GetStdHandle = ctypes.WINFUNCTYPE(
        ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD)(
        (b"GetStdHandle", ctypes.windll.kernel32))
    h = GetStdHandle(WIN_OUTPUT_IDS[fileno])

    WriteConsoleW = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HANDLE, ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.wintypes.LPVOID)((b"WriteConsoleW", ctypes.windll.kernel32))
    written = ctypes.wintypes.DWORD(0)

    GetFileType = ctypes.WINFUNCTYPE(ctypes.wintypes.DWORD, ctypes.wintypes.DWORD)((b"GetFileType", ctypes.windll.kernel32))
    FILE_TYPE_CHAR = 0x0002
    FILE_TYPE_REMOTE = 0x8000
    GetConsoleMode = ctypes.WINFUNCTYPE(
        ctypes.wintypes.BOOL, ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.DWORD))(
        (b"GetConsoleMode", ctypes.windll.kernel32))
    INVALID_HANDLE_VALUE = ctypes.wintypes.DWORD(-1).value

    def not_a_console(handle):
        if handle == INVALID_HANDLE_VALUE or handle is None:
            return True
        return ((GetFileType(handle) & ~FILE_TYPE_REMOTE) != FILE_TYPE_CHAR or
                GetConsoleMode(handle, ctypes.byref(ctypes.wintypes.DWORD())) == 0)

    if not_a_console(h):
        return False

    def next_nonbmp_pos(s):
        try:
            return next(i for i, c in enumerate(s) if ord(c) > 0xffff)
        except StopIteration:
            return len(s)

    while s:
        count = min(next_nonbmp_pos(s), 1024)

        ret = WriteConsoleW(
            h, s, count if count else 2, ctypes.byref(written), None)
        if ret == 0:
            raise OSError('Failed to write string')
        if not count:  # We just wrote a non-BMP character
            assert written.value == 2
            s = s[1:]
        else:
            assert written.value > 0
            s = s[written.value:]
    return True


def write_string(s, out=None, encoding=None):
    if out is None:
        out = sys.stderr
    assert type(s) == compat_str

    if sys.platform == 'win32' and encoding is None and hasattr(out, 'fileno'):
        if _windows_write_string(s, out):
            return

    if ('b' in getattr(out, 'mode', '') or
            sys.version_info[0] < 3):  # Python 2 lies about mode of sys.stderr
        byt = s.encode(encoding or preferredencoding(), 'ignore')
        out.write(byt)
    elif hasattr(out, 'buffer'):
        enc = encoding or getattr(out, 'encoding', None) or preferredencoding()
        byt = s.encode(enc, 'ignore')
        out.buffer.write(byt)
    else:
        out.write(s)
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
    return struct_pack('%dB' % len(xs), *xs)


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
        fcntl.flock(f, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)

    def _unlock_file(f):
        fcntl.flock(f, fcntl.LOCK_UN)


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


def get_filesystem_encoding():
    encoding = sys.getfilesystemencoding()
    return encoding if encoding is not None else 'utf-8'


def shell_quote(args):
    quoted_args = []
    encoding = get_filesystem_encoding()
    for a in args:
        if isinstance(a, bytes):
            # We may get a filename encoded with 'encodeFilename'
            a = a.decode(encoding)
        quoted_args.append(pipes.quote(a))
    return ' '.join(quoted_args)


def smuggle_url(url, data):
    """ Pass additional data in a URL for internal use. """

    sdata = compat_urllib_parse.urlencode(
        {'__youtubedl_smuggle': json.dumps(data)})
    return url + '#' + sdata


def unsmuggle_url(smug_url, default=None):
    if '#__youtubedl_smuggle' not in smug_url:
        return smug_url, default
    url, _, sdata = smug_url.rpartition('#')
    jsond = compat_parse_qs(sdata)['__youtubedl_smuggle'][0]
    data = json.loads(jsond)
    return url, data


def format_bytes(bytes):
    if bytes is None:
        return 'N/A'
    if type(bytes) is str:
        bytes = float(bytes)
    if bytes == 0.0:
        exponent = 0
    else:
        exponent = int(math.log(bytes, 1024.0))
    suffix = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'][exponent]
    converted = float(bytes) / float(1024 ** exponent)
    return '%.2f%s' % (converted, suffix)


def parse_filesize(s):
    if s is None:
        return None

    # The lower-case forms are of course incorrect and inofficial,
    # but we support those too
    _UNIT_TABLE = {
        'B': 1,
        'b': 1,
        'KiB': 1024,
        'KB': 1000,
        'kB': 1024,
        'Kb': 1000,
        'MiB': 1024 ** 2,
        'MB': 1000 ** 2,
        'mB': 1024 ** 2,
        'Mb': 1000 ** 2,
        'GiB': 1024 ** 3,
        'GB': 1000 ** 3,
        'gB': 1024 ** 3,
        'Gb': 1000 ** 3,
        'TiB': 1024 ** 4,
        'TB': 1000 ** 4,
        'tB': 1024 ** 4,
        'Tb': 1000 ** 4,
        'PiB': 1024 ** 5,
        'PB': 1000 ** 5,
        'pB': 1024 ** 5,
        'Pb': 1000 ** 5,
        'EiB': 1024 ** 6,
        'EB': 1000 ** 6,
        'eB': 1024 ** 6,
        'Eb': 1000 ** 6,
        'ZiB': 1024 ** 7,
        'ZB': 1000 ** 7,
        'zB': 1024 ** 7,
        'Zb': 1000 ** 7,
        'YiB': 1024 ** 8,
        'YB': 1000 ** 8,
        'yB': 1024 ** 8,
        'Yb': 1000 ** 8,
    }

    units_re = '|'.join(re.escape(u) for u in _UNIT_TABLE)
    m = re.match(
        r'(?P<num>[0-9]+(?:[,.][0-9]*)?)\s*(?P<unit>%s)' % units_re, s)
    if not m:
        return None

    num_str = m.group('num').replace(',', '.')
    mult = _UNIT_TABLE[m.group('unit')]
    return int(float(num_str) * mult)


def month_by_name(name):
    """ Return the number of a month by (locale-independently) English name """

    try:
        return ENGLISH_MONTH_NAMES.index(name) + 1
    except ValueError:
        return None


def month_by_abbreviation(abbrev):
    """ Return the number of a month by (locale-independently) English
        abbreviations """

    try:
        return [s[:3] for s in ENGLISH_MONTH_NAMES].index(abbrev) + 1
    except ValueError:
        return None


def fix_xml_ampersands(xml_str):
    """Replace all the '&' by '&amp;' in XML"""
    return re.sub(
        r'&(?!amp;|lt;|gt;|apos;|quot;|#x[0-9a-fA-F]{,4};|#[0-9]{,4};)',
        '&amp;',
        xml_str)


def setproctitle(title):
    assert isinstance(title, compat_str)
    try:
        libc = ctypes.cdll.LoadLibrary("libc.so.6")
    except OSError:
        return
    title_bytes = title.encode('utf-8')
    buf = ctypes.create_string_buffer(len(title_bytes))
    buf.value = title_bytes
    try:
        libc.prctl(15, buf, 0, 0, 0)
    except AttributeError:
        return  # Strange libc, just skip this


def remove_start(s, start):
    if s.startswith(start):
        return s[len(start):]
    return s


def remove_end(s, end):
    if s.endswith(end):
        return s[:-len(end)]
    return s


def url_basename(url):
    path = compat_urlparse.urlparse(url).path
    return path.strip('/').split('/')[-1]


class HEADRequest(compat_urllib_request.Request):
    def get_method(self):
        return "HEAD"


def int_or_none(v, scale=1, default=None, get_attr=None, invscale=1):
    if get_attr:
        if v is not None:
            v = getattr(v, get_attr, None)
    if v == '':
        v = None
    if v is None:
        return default
    try:
        return int(v) * invscale // scale
    except ValueError:
        return default


def str_or_none(v, default=None):
    return default if v is None else compat_str(v)


def str_to_int(int_str):
    """ A more relaxed version of int_or_none """
    if int_str is None:
        return None
    int_str = re.sub(r'[,\.\+]', '', int_str)
    return int(int_str)


def float_or_none(v, scale=1, invscale=1, default=None):
    if v is None:
        return default
    try:
        return float(v) * invscale / scale
    except ValueError:
        return default


def parse_duration(s):
    if not isinstance(s, compat_basestring):
        return None

    s = s.strip()

    m = re.match(
        r'''(?ix)(?:P?T)?
        (?:
            (?P<only_mins>[0-9.]+)\s*(?:mins?\.?|minutes?)\s*|
            (?P<only_hours>[0-9.]+)\s*(?:hours?)|

            \s*(?P<hours_reversed>[0-9]+)\s*(?:[:h]|hours?)\s*(?P<mins_reversed>[0-9]+)\s*(?:[:m]|mins?\.?|minutes?)\s*|
            (?:
                (?:
                    (?:(?P<days>[0-9]+)\s*(?:[:d]|days?)\s*)?
                    (?P<hours>[0-9]+)\s*(?:[:h]|hours?)\s*
                )?
                (?P<mins>[0-9]+)\s*(?:[:m]|mins?|minutes?)\s*
            )?
            (?P<secs>[0-9]+)(?P<ms>\.[0-9]+)?\s*(?:s|secs?|seconds?)?
        )$''', s)
    if not m:
        return None
    res = 0
    if m.group('only_mins'):
        return float_or_none(m.group('only_mins'), invscale=60)
    if m.group('only_hours'):
        return float_or_none(m.group('only_hours'), invscale=60 * 60)
    if m.group('secs'):
        res += int(m.group('secs'))
    if m.group('mins_reversed'):
        res += int(m.group('mins_reversed')) * 60
    if m.group('mins'):
        res += int(m.group('mins')) * 60
    if m.group('hours'):
        res += int(m.group('hours')) * 60 * 60
    if m.group('hours_reversed'):
        res += int(m.group('hours_reversed')) * 60 * 60
    if m.group('days'):
        res += int(m.group('days')) * 24 * 60 * 60
    if m.group('ms'):
        res += float(m.group('ms'))
    return res


def prepend_extension(filename, ext, expected_real_ext=None):
    name, real_ext = os.path.splitext(filename)
    return (
        '{0}.{1}{2}'.format(name, ext, real_ext)
        if not expected_real_ext or real_ext[1:] == expected_real_ext
        else '{0}.{1}'.format(filename, ext))


def replace_extension(filename, ext, expected_real_ext=None):
    name, real_ext = os.path.splitext(filename)
    return '{0}.{1}'.format(
        name if not expected_real_ext or real_ext[1:] == expected_real_ext else filename,
        ext)


def check_executable(exe, args=[]):
    """ Checks if the given binary is installed somewhere in PATH, and returns its name.
    args can be a list of arguments for a short output (like -version) """
    try:
        subprocess.Popen([exe] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    except OSError:
        return False
    return exe


def get_exe_version(exe, args=['--version'],
                    version_re=None, unrecognized='present'):
    """ Returns the version of the specified executable,
    or False if the executable is not present """
    try:
        out, _ = subprocess.Popen(
            [encodeArgument(exe)] + args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
    except OSError:
        return False
    if isinstance(out, bytes):  # Python 2.x
        out = out.decode('ascii', 'ignore')
    return detect_exe_version(out, version_re, unrecognized)


def detect_exe_version(output, version_re=None, unrecognized='present'):
    assert isinstance(output, compat_str)
    if version_re is None:
        version_re = r'version\s+([-0-9._a-zA-Z]+)'
    m = re.search(version_re, output)
    if m:
        return m.group(1)
    else:
        return unrecognized


class PagedList(object):
    def __len__(self):
        # This is only useful for tests
        return len(self.getslice())


class OnDemandPagedList(PagedList):
    def __init__(self, pagefunc, pagesize):
        self._pagefunc = pagefunc
        self._pagesize = pagesize

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


class InAdvancePagedList(PagedList):
    def __init__(self, pagefunc, pagecount, pagesize):
        self._pagefunc = pagefunc
        self._pagecount = pagecount
        self._pagesize = pagesize

    def getslice(self, start=0, end=None):
        res = []
        start_page = start // self._pagesize
        end_page = (
            self._pagecount if end is None else (end // self._pagesize + 1))
        skip_elems = start - start_page * self._pagesize
        only_more = None if end is None else end - start
        for pagenum in range(start_page, end_page):
            page = list(self._pagefunc(pagenum))
            if skip_elems:
                page = page[skip_elems:]
                skip_elems = None
            if only_more is not None:
                if len(page) < only_more:
                    only_more -= len(page)
                else:
                    page = page[:only_more]
                    res.extend(page)
                    break
            res.extend(page)
        return res


def uppercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\U[0-9a-fA-F]{8}',
        lambda m: unicode_escape(m.group(0))[0],
        s)


def lowercase_escape(s):
    unicode_escape = codecs.getdecoder('unicode_escape')
    return re.sub(
        r'\\u[0-9a-fA-F]{4}',
        lambda m: unicode_escape(m.group(0))[0],
        s)


def escape_rfc3986(s):
    """Escape non-ASCII characters as suggested by RFC 3986"""
    if sys.version_info < (3, 0) and isinstance(s, compat_str):
        s = s.encode('utf-8')
    return compat_urllib_parse.quote(s, b"%/;:@&=+$,!~*'()?#[]")


def escape_url(url):
    """Escape URL as suggested by RFC 3986"""
    url_parsed = compat_urllib_parse_urlparse(url)
    return url_parsed._replace(
        path=escape_rfc3986(url_parsed.path),
        params=escape_rfc3986(url_parsed.params),
        query=escape_rfc3986(url_parsed.query),
        fragment=escape_rfc3986(url_parsed.fragment)
    ).geturl()

try:
    struct.pack('!I', 0)
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
        BOM_UTF8 = '\xef\xbb\xbf'
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


def encode_dict(d, encoding='utf-8'):
    return dict((k.encode(encoding), v.encode(encoding)) for k, v in d.items())


US_RATINGS = {
    'G': 0,
    'PG': 10,
    'PG-13': 13,
    'R': 16,
    'NC': 18,
}


def parse_age_limit(s):
    if s is None:
        return None
    m = re.match(r'^(?P<age>\d{1,2})\+?$', s)
    return int(m.group('age')) if m else US_RATINGS.get(s, None)


def strip_jsonp(code):
    return re.sub(
        r'(?s)^[a-zA-Z0-9_]+\s*\(\s*(.*)\);?\s*?(?://[^\n]*)*$', r'\1', code)


def js_to_json(code):
    def fix_kv(m):
        v = m.group(0)
        if v in ('true', 'false', 'null'):
            return v
        if v.startswith('"'):
            v = re.sub(r"\\'", "'", v[1:-1])
        elif v.startswith("'"):
            v = v[1:-1]
            v = re.sub(r"\\\\|\\'|\"", lambda m: {
                '\\\\': '\\\\',
                "\\'": "'",
                '"': '\\"',
            }[m.group(0)], v)
        return '"%s"' % v

    res = re.sub(r'''(?x)
        "(?:[^"\\]*(?:\\\\|\\['"nu]))*[^"\\]*"|
        '(?:[^'\\]*(?:\\\\|\\['"nu]))*[^'\\]*'|
        [a-zA-Z_][.a-zA-Z_0-9]*
        ''', fix_kv, code)
    res = re.sub(r',(\s*[\]}])', lambda m: m.group(1), res)
    return res


def qualities(quality_ids):
    """ Get a numeric quality value out of a list of possible values """
    def q(qid):
        try:
            return quality_ids.index(qid)
        except ValueError:
            return -1
    return q


DEFAULT_OUTTMPL = '%(title)s-%(id)s.%(ext)s'


def limit_length(s, length):
    """ Add ellipses to overly long strings """
    if s is None:
        return None
    ELLIPSES = '...'
    if len(s) > length:
        return s[:length - len(ELLIPSES)] + ELLIPSES
    return s


def version_tuple(v):
    return tuple(int(e) for e in re.split(r'[-.]', v))


def is_outdated_version(version, limit, assume_new=True):
    if not version:
        return not assume_new
    try:
        return version_tuple(version) < version_tuple(limit)
    except ValueError:
        return not assume_new


def ytdl_is_updateable():
    """ Returns if youtube-dl can be updated with -U """
    from zipimport import zipimporter

    return isinstance(globals().get('__loader__'), zipimporter) or hasattr(sys, 'frozen')


def args_to_str(args):
    # Get a short string representation for a subprocess command
    return ' '.join(shlex_quote(a) for a in args)


def mimetype2ext(mt):
    _, _, res = mt.rpartition('/')

    return {
        'x-ms-wmv': 'wmv',
        'x-mp4-fragmented': 'mp4',
        'ttml+xml': 'ttml',
    }.get(res, res)


def urlhandle_detect_ext(url_handle):
    try:
        url_handle.headers
        getheader = lambda h: url_handle.headers[h]
    except AttributeError:  # Python < 3
        getheader = url_handle.info().getheader

    cd = getheader('Content-Disposition')
    if cd:
        m = re.match(r'attachment;\s*filename="(?P<filename>[^"]+)"', cd)
        if m:
            e = determine_ext(m.group('filename'), default_ext=None)
            if e:
                return e

    return mimetype2ext(getheader('Content-Type'))


def encode_data_uri(data, mime_type):
    return 'data:%s;base64,%s' % (mime_type, base64.b64encode(data).decode('ascii'))


def age_restricted(content_limit, age_limit):
    """ Returns True iff the content should be blocked """

    if age_limit is None:  # No limit set
        return False
    if content_limit is None:
        return False  # Content available for everyone
    return age_limit < content_limit


def is_html(first_bytes):
    """ Detect whether a file contains HTML by examining its first bytes. """

    BOMS = [
        (b'\xef\xbb\xbf', 'utf-8'),
        (b'\x00\x00\xfe\xff', 'utf-32-be'),
        (b'\xff\xfe\x00\x00', 'utf-32-le'),
        (b'\xff\xfe', 'utf-16-le'),
        (b'\xfe\xff', 'utf-16-be'),
    ]
    for bom, enc in BOMS:
        if first_bytes.startswith(bom):
            s = first_bytes[len(bom):].decode(enc, 'replace')
            break
    else:
        s = first_bytes.decode('utf-8', 'replace')

    return re.match(r'^\s*<', s)


def determine_protocol(info_dict):
    protocol = info_dict.get('protocol')
    if protocol is not None:
        return protocol

    url = info_dict['url']
    if url.startswith('rtmp'):
        return 'rtmp'
    elif url.startswith('mms'):
        return 'mms'
    elif url.startswith('rtsp'):
        return 'rtsp'

    ext = determine_ext(url)
    if ext == 'm3u8':
        return 'm3u8'
    elif ext == 'f4m':
        return 'f4m'

    return compat_urllib_parse_urlparse(url).scheme


def render_table(header_row, data):
    """ Render a list of rows, each as a list of values """
    table = [header_row] + data
    max_lens = [max(len(compat_str(v)) for v in col) for col in zip(*table)]
    format_str = ' '.join('%-' + compat_str(ml + 1) + 's' for ml in max_lens[:-1]) + '%s'
    return '\n'.join(format_str % tuple(row) for row in table)


def _match_one(filter_part, dct):
    COMPARISON_OPERATORS = {
        '<': operator.lt,
        '<=': operator.le,
        '>': operator.gt,
        '>=': operator.ge,
        '=': operator.eq,
        '!=': operator.ne,
    }
    operator_rex = re.compile(r'''(?x)\s*
        (?P<key>[a-z_]+)
        \s*(?P<op>%s)(?P<none_inclusive>\s*\?)?\s*
        (?:
            (?P<intval>[0-9.]+(?:[kKmMgGtTpPeEzZyY]i?[Bb]?)?)|
            (?P<strval>(?![0-9.])[a-z0-9A-Z]*)
        )
        \s*$
        ''' % '|'.join(map(re.escape, COMPARISON_OPERATORS.keys())))
    m = operator_rex.search(filter_part)
    if m:
        op = COMPARISON_OPERATORS[m.group('op')]
        if m.group('strval') is not None:
            if m.group('op') not in ('=', '!='):
                raise ValueError(
                    'Operator %s does not support string values!' % m.group('op'))
            comparison_value = m.group('strval')
        else:
            try:
                comparison_value = int(m.group('intval'))
            except ValueError:
                comparison_value = parse_filesize(m.group('intval'))
                if comparison_value is None:
                    comparison_value = parse_filesize(m.group('intval') + 'B')
                if comparison_value is None:
                    raise ValueError(
                        'Invalid integer value %r in filter part %r' % (
                            m.group('intval'), filter_part))
        actual_value = dct.get(m.group('key'))
        if actual_value is None:
            return m.group('none_inclusive')
        return op(actual_value, comparison_value)

    UNARY_OPERATORS = {
        '': lambda v: v is not None,
        '!': lambda v: v is None,
    }
    operator_rex = re.compile(r'''(?x)\s*
        (?P<op>%s)\s*(?P<key>[a-z_]+)
        \s*$
        ''' % '|'.join(map(re.escape, UNARY_OPERATORS.keys())))
    m = operator_rex.search(filter_part)
    if m:
        op = UNARY_OPERATORS[m.group('op')]
        actual_value = dct.get(m.group('key'))
        return op(actual_value)

    raise ValueError('Invalid filter part %r' % filter_part)


def match_str(filter_str, dct):
    """ Filter a dictionary with a simple string syntax. Returns True (=passes filter) or false """

    return all(
        _match_one(filter_part, dct) for filter_part in filter_str.split('&'))


def match_filter_func(filter_str):
    def _match_func(info_dict):
        if match_str(filter_str, info_dict):
            return None
        else:
            video_title = info_dict.get('title', info_dict.get('id', 'video'))
            return '%s does not pass filter %s, skipping ..' % (video_title, filter_str)
    return _match_func


def parse_dfxp_time_expr(time_expr):
    if not time_expr:
        return 0.0

    mobj = re.match(r'^(?P<time_offset>\d+(?:\.\d+)?)s?$', time_expr)
    if mobj:
        return float(mobj.group('time_offset'))

    mobj = re.match(r'^(\d+):(\d\d):(\d\d(?:\.\d+)?)$', time_expr)
    if mobj:
        return 3600 * int(mobj.group(1)) + 60 * int(mobj.group(2)) + float(mobj.group(3))


def srt_subtitles_timecode(seconds):
    return '%02d:%02d:%02d,%03d' % (seconds / 3600, (seconds % 3600) / 60, seconds % 60, (seconds % 1) * 1000)


def dfxp2srt(dfxp_data):
    _x = functools.partial(xpath_with_ns, ns_map={
        'ttml': 'http://www.w3.org/ns/ttml',
        'ttaf1': 'http://www.w3.org/2006/10/ttaf1',
    })

    def parse_node(node):
        str_or_empty = functools.partial(str_or_none, default='')

        out = str_or_empty(node.text)

        for child in node:
            if child.tag in (_x('ttml:br'), _x('ttaf1:br'), 'br'):
                out += '\n' + str_or_empty(child.tail)
            elif child.tag in (_x('ttml:span'), _x('ttaf1:span'), 'span'):
                out += str_or_empty(parse_node(child))
            else:
                out += str_or_empty(xml.etree.ElementTree.tostring(child))

        return out

    dfxp = compat_etree_fromstring(dfxp_data.encode('utf-8'))
    out = []
    paras = dfxp.findall(_x('.//ttml:p')) or dfxp.findall(_x('.//ttaf1:p')) or dfxp.findall('.//p')

    if not paras:
        raise ValueError('Invalid dfxp/TTML subtitle')

    for para, index in zip(paras, itertools.count(1)):
        begin_time = parse_dfxp_time_expr(para.attrib['begin'])
        end_time = parse_dfxp_time_expr(para.attrib.get('end'))
        if not end_time:
            end_time = begin_time + parse_dfxp_time_expr(para.attrib['dur'])
        out.append('%d\n%s --> %s\n%s\n\n' % (
            index,
            srt_subtitles_timecode(begin_time),
            srt_subtitles_timecode(end_time),
            parse_node(para)))

    return ''.join(out)


def cli_option(params, command_option, param):
    param = params.get(param)
    return [command_option, param] if param is not None else []


def cli_bool_option(params, command_option, param, true_value='true', false_value='false', separator=None):
    param = params.get(param)
    assert isinstance(param, bool)
    if separator:
        return [command_option + separator + (true_value if param else false_value)]
    return [command_option, true_value if param else false_value]


def cli_valueless_option(params, command_option, param, expected_value=True):
    param = params.get(param)
    return [command_option] if param == expected_value else []


def cli_configuration_args(params, param, default=[]):
    ex_args = params.get(param)
    if ex_args is None:
        return default
    assert isinstance(ex_args, list)
    return ex_args


class ISO639Utils(object):
    # See http://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt
    _lang_map = {
        'aa': 'aar',
        'ab': 'abk',
        'ae': 'ave',
        'af': 'afr',
        'ak': 'aka',
        'am': 'amh',
        'an': 'arg',
        'ar': 'ara',
        'as': 'asm',
        'av': 'ava',
        'ay': 'aym',
        'az': 'aze',
        'ba': 'bak',
        'be': 'bel',
        'bg': 'bul',
        'bh': 'bih',
        'bi': 'bis',
        'bm': 'bam',
        'bn': 'ben',
        'bo': 'bod',
        'br': 'bre',
        'bs': 'bos',
        'ca': 'cat',
        'ce': 'che',
        'ch': 'cha',
        'co': 'cos',
        'cr': 'cre',
        'cs': 'ces',
        'cu': 'chu',
        'cv': 'chv',
        'cy': 'cym',
        'da': 'dan',
        'de': 'deu',
        'dv': 'div',
        'dz': 'dzo',
        'ee': 'ewe',
        'el': 'ell',
        'en': 'eng',
        'eo': 'epo',
        'es': 'spa',
        'et': 'est',
        'eu': 'eus',
        'fa': 'fas',
        'ff': 'ful',
        'fi': 'fin',
        'fj': 'fij',
        'fo': 'fao',
        'fr': 'fra',
        'fy': 'fry',
        'ga': 'gle',
        'gd': 'gla',
        'gl': 'glg',
        'gn': 'grn',
        'gu': 'guj',
        'gv': 'glv',
        'ha': 'hau',
        'he': 'heb',
        'hi': 'hin',
        'ho': 'hmo',
        'hr': 'hrv',
        'ht': 'hat',
        'hu': 'hun',
        'hy': 'hye',
        'hz': 'her',
        'ia': 'ina',
        'id': 'ind',
        'ie': 'ile',
        'ig': 'ibo',
        'ii': 'iii',
        'ik': 'ipk',
        'io': 'ido',
        'is': 'isl',
        'it': 'ita',
        'iu': 'iku',
        'ja': 'jpn',
        'jv': 'jav',
        'ka': 'kat',
        'kg': 'kon',
        'ki': 'kik',
        'kj': 'kua',
        'kk': 'kaz',
        'kl': 'kal',
        'km': 'khm',
        'kn': 'kan',
        'ko': 'kor',
        'kr': 'kau',
        'ks': 'kas',
        'ku': 'kur',
        'kv': 'kom',
        'kw': 'cor',
        'ky': 'kir',
        'la': 'lat',
        'lb': 'ltz',
        'lg': 'lug',
        'li': 'lim',
        'ln': 'lin',
        'lo': 'lao',
        'lt': 'lit',
        'lu': 'lub',
        'lv': 'lav',
        'mg': 'mlg',
        'mh': 'mah',
        'mi': 'mri',
        'mk': 'mkd',
        'ml': 'mal',
        'mn': 'mon',
        'mr': 'mar',
        'ms': 'msa',
        'mt': 'mlt',
        'my': 'mya',
        'na': 'nau',
        'nb': 'nob',
        'nd': 'nde',
        'ne': 'nep',
        'ng': 'ndo',
        'nl': 'nld',
        'nn': 'nno',
        'no': 'nor',
        'nr': 'nbl',
        'nv': 'nav',
        'ny': 'nya',
        'oc': 'oci',
        'oj': 'oji',
        'om': 'orm',
        'or': 'ori',
        'os': 'oss',
        'pa': 'pan',
        'pi': 'pli',
        'pl': 'pol',
        'ps': 'pus',
        'pt': 'por',
        'qu': 'que',
        'rm': 'roh',
        'rn': 'run',
        'ro': 'ron',
        'ru': 'rus',
        'rw': 'kin',
        'sa': 'san',
        'sc': 'srd',
        'sd': 'snd',
        'se': 'sme',
        'sg': 'sag',
        'si': 'sin',
        'sk': 'slk',
        'sl': 'slv',
        'sm': 'smo',
        'sn': 'sna',
        'so': 'som',
        'sq': 'sqi',
        'sr': 'srp',
        'ss': 'ssw',
        'st': 'sot',
        'su': 'sun',
        'sv': 'swe',
        'sw': 'swa',
        'ta': 'tam',
        'te': 'tel',
        'tg': 'tgk',
        'th': 'tha',
        'ti': 'tir',
        'tk': 'tuk',
        'tl': 'tgl',
        'tn': 'tsn',
        'to': 'ton',
        'tr': 'tur',
        'ts': 'tso',
        'tt': 'tat',
        'tw': 'twi',
        'ty': 'tah',
        'ug': 'uig',
        'uk': 'ukr',
        'ur': 'urd',
        'uz': 'uzb',
        've': 'ven',
        'vi': 'vie',
        'vo': 'vol',
        'wa': 'wln',
        'wo': 'wol',
        'xh': 'xho',
        'yi': 'yid',
        'yo': 'yor',
        'za': 'zha',
        'zh': 'zho',
        'zu': 'zul',
    }

    @classmethod
    def short2long(cls, code):
        """Convert language code from ISO 639-1 to ISO 639-2/T"""
        return cls._lang_map.get(code[:2])

    @classmethod
    def long2short(cls, code):
        """Convert language code from ISO 639-2/T to ISO 639-1"""
        for short_name, long_name in cls._lang_map.items():
            if long_name == code:
                return short_name


class ISO3166Utils(object):
    # From http://data.okfn.org/data/core/country-list
    _country_map = {
        'AF': 'Afghanistan',
        'AX': 'Åland Islands',
        'AL': 'Albania',
        'DZ': 'Algeria',
        'AS': 'American Samoa',
        'AD': 'Andorra',
        'AO': 'Angola',
        'AI': 'Anguilla',
        'AQ': 'Antarctica',
        'AG': 'Antigua and Barbuda',
        'AR': 'Argentina',
        'AM': 'Armenia',
        'AW': 'Aruba',
        'AU': 'Australia',
        'AT': 'Austria',
        'AZ': 'Azerbaijan',
        'BS': 'Bahamas',
        'BH': 'Bahrain',
        'BD': 'Bangladesh',
        'BB': 'Barbados',
        'BY': 'Belarus',
        'BE': 'Belgium',
        'BZ': 'Belize',
        'BJ': 'Benin',
        'BM': 'Bermuda',
        'BT': 'Bhutan',
        'BO': 'Bolivia, Plurinational State of',
        'BQ': 'Bonaire, Sint Eustatius and Saba',
        'BA': 'Bosnia and Herzegovina',
        'BW': 'Botswana',
        'BV': 'Bouvet Island',
        'BR': 'Brazil',
        'IO': 'British Indian Ocean Territory',
        'BN': 'Brunei Darussalam',
        'BG': 'Bulgaria',
        'BF': 'Burkina Faso',
        'BI': 'Burundi',
        'KH': 'Cambodia',
        'CM': 'Cameroon',
        'CA': 'Canada',
        'CV': 'Cape Verde',
        'KY': 'Cayman Islands',
        'CF': 'Central African Republic',
        'TD': 'Chad',
        'CL': 'Chile',
        'CN': 'China',
        'CX': 'Christmas Island',
        'CC': 'Cocos (Keeling) Islands',
        'CO': 'Colombia',
        'KM': 'Comoros',
        'CG': 'Congo',
        'CD': 'Congo, the Democratic Republic of the',
        'CK': 'Cook Islands',
        'CR': 'Costa Rica',
        'CI': 'Côte d\'Ivoire',
        'HR': 'Croatia',
        'CU': 'Cuba',
        'CW': 'Curaçao',
        'CY': 'Cyprus',
        'CZ': 'Czech Republic',
        'DK': 'Denmark',
        'DJ': 'Djibouti',
        'DM': 'Dominica',
        'DO': 'Dominican Republic',
        'EC': 'Ecuador',
        'EG': 'Egypt',
        'SV': 'El Salvador',
        'GQ': 'Equatorial Guinea',
        'ER': 'Eritrea',
        'EE': 'Estonia',
        'ET': 'Ethiopia',
        'FK': 'Falkland Islands (Malvinas)',
        'FO': 'Faroe Islands',
        'FJ': 'Fiji',
        'FI': 'Finland',
        'FR': 'France',
        'GF': 'French Guiana',
        'PF': 'French Polynesia',
        'TF': 'French Southern Territories',
        'GA': 'Gabon',
        'GM': 'Gambia',
        'GE': 'Georgia',
        'DE': 'Germany',
        'GH': 'Ghana',
        'GI': 'Gibraltar',
        'GR': 'Greece',
        'GL': 'Greenland',
        'GD': 'Grenada',
        'GP': 'Guadeloupe',
        'GU': 'Guam',
        'GT': 'Guatemala',
        'GG': 'Guernsey',
        'GN': 'Guinea',
        'GW': 'Guinea-Bissau',
        'GY': 'Guyana',
        'HT': 'Haiti',
        'HM': 'Heard Island and McDonald Islands',
        'VA': 'Holy See (Vatican City State)',
        'HN': 'Honduras',
        'HK': 'Hong Kong',
        'HU': 'Hungary',
        'IS': 'Iceland',
        'IN': 'India',
        'ID': 'Indonesia',
        'IR': 'Iran, Islamic Republic of',
        'IQ': 'Iraq',
        'IE': 'Ireland',
        'IM': 'Isle of Man',
        'IL': 'Israel',
        'IT': 'Italy',
        'JM': 'Jamaica',
        'JP': 'Japan',
        'JE': 'Jersey',
        'JO': 'Jordan',
        'KZ': 'Kazakhstan',
        'KE': 'Kenya',
        'KI': 'Kiribati',
        'KP': 'Korea, Democratic People\'s Republic of',
        'KR': 'Korea, Republic of',
        'KW': 'Kuwait',
        'KG': 'Kyrgyzstan',
        'LA': 'Lao People\'s Democratic Republic',
        'LV': 'Latvia',
        'LB': 'Lebanon',
        'LS': 'Lesotho',
        'LR': 'Liberia',
        'LY': 'Libya',
        'LI': 'Liechtenstein',
        'LT': 'Lithuania',
        'LU': 'Luxembourg',
        'MO': 'Macao',
        'MK': 'Macedonia, the Former Yugoslav Republic of',
        'MG': 'Madagascar',
        'MW': 'Malawi',
        'MY': 'Malaysia',
        'MV': 'Maldives',
        'ML': 'Mali',
        'MT': 'Malta',
        'MH': 'Marshall Islands',
        'MQ': 'Martinique',
        'MR': 'Mauritania',
        'MU': 'Mauritius',
        'YT': 'Mayotte',
        'MX': 'Mexico',
        'FM': 'Micronesia, Federated States of',
        'MD': 'Moldova, Republic of',
        'MC': 'Monaco',
        'MN': 'Mongolia',
        'ME': 'Montenegro',
        'MS': 'Montserrat',
        'MA': 'Morocco',
        'MZ': 'Mozambique',
        'MM': 'Myanmar',
        'NA': 'Namibia',
        'NR': 'Nauru',
        'NP': 'Nepal',
        'NL': 'Netherlands',
        'NC': 'New Caledonia',
        'NZ': 'New Zealand',
        'NI': 'Nicaragua',
        'NE': 'Niger',
        'NG': 'Nigeria',
        'NU': 'Niue',
        'NF': 'Norfolk Island',
        'MP': 'Northern Mariana Islands',
        'NO': 'Norway',
        'OM': 'Oman',
        'PK': 'Pakistan',
        'PW': 'Palau',
        'PS': 'Palestine, State of',
        'PA': 'Panama',
        'PG': 'Papua New Guinea',
        'PY': 'Paraguay',
        'PE': 'Peru',
        'PH': 'Philippines',
        'PN': 'Pitcairn',
        'PL': 'Poland',
        'PT': 'Portugal',
        'PR': 'Puerto Rico',
        'QA': 'Qatar',
        'RE': 'Réunion',
        'RO': 'Romania',
        'RU': 'Russian Federation',
        'RW': 'Rwanda',
        'BL': 'Saint Barthélemy',
        'SH': 'Saint Helena, Ascension and Tristan da Cunha',
        'KN': 'Saint Kitts and Nevis',
        'LC': 'Saint Lucia',
        'MF': 'Saint Martin (French part)',
        'PM': 'Saint Pierre and Miquelon',
        'VC': 'Saint Vincent and the Grenadines',
        'WS': 'Samoa',
        'SM': 'San Marino',
        'ST': 'Sao Tome and Principe',
        'SA': 'Saudi Arabia',
        'SN': 'Senegal',
        'RS': 'Serbia',
        'SC': 'Seychelles',
        'SL': 'Sierra Leone',
        'SG': 'Singapore',
        'SX': 'Sint Maarten (Dutch part)',
        'SK': 'Slovakia',
        'SI': 'Slovenia',
        'SB': 'Solomon Islands',
        'SO': 'Somalia',
        'ZA': 'South Africa',
        'GS': 'South Georgia and the South Sandwich Islands',
        'SS': 'South Sudan',
        'ES': 'Spain',
        'LK': 'Sri Lanka',
        'SD': 'Sudan',
        'SR': 'Suriname',
        'SJ': 'Svalbard and Jan Mayen',
        'SZ': 'Swaziland',
        'SE': 'Sweden',
        'CH': 'Switzerland',
        'SY': 'Syrian Arab Republic',
        'TW': 'Taiwan, Province of China',
        'TJ': 'Tajikistan',
        'TZ': 'Tanzania, United Republic of',
        'TH': 'Thailand',
        'TL': 'Timor-Leste',
        'TG': 'Togo',
        'TK': 'Tokelau',
        'TO': 'Tonga',
        'TT': 'Trinidad and Tobago',
        'TN': 'Tunisia',
        'TR': 'Turkey',
        'TM': 'Turkmenistan',
        'TC': 'Turks and Caicos Islands',
        'TV': 'Tuvalu',
        'UG': 'Uganda',
        'UA': 'Ukraine',
        'AE': 'United Arab Emirates',
        'GB': 'United Kingdom',
        'US': 'United States',
        'UM': 'United States Minor Outlying Islands',
        'UY': 'Uruguay',
        'UZ': 'Uzbekistan',
        'VU': 'Vanuatu',
        'VE': 'Venezuela, Bolivarian Republic of',
        'VN': 'Viet Nam',
        'VG': 'Virgin Islands, British',
        'VI': 'Virgin Islands, U.S.',
        'WF': 'Wallis and Futuna',
        'EH': 'Western Sahara',
        'YE': 'Yemen',
        'ZM': 'Zambia',
        'ZW': 'Zimbabwe',
    }

    @classmethod
    def short2full(cls, code):
        """Convert an ISO 3166-2 country code to the corresponding full name"""
        return cls._country_map.get(code.upper())


class PerRequestProxyHandler(compat_urllib_request.ProxyHandler):
    def __init__(self, proxies=None):
        # Set default handlers
        for type in ('http', 'https'):
            setattr(self, '%s_open' % type,
                    lambda r, proxy='__noproxy__', type=type, meth=self.proxy_open:
                        meth(r, proxy, type))
        return compat_urllib_request.ProxyHandler.__init__(self, proxies)

    def proxy_open(self, req, proxy, type):
        req_proxy = req.headers.get('Ytdl-request-proxy')
        if req_proxy is not None:
            proxy = req_proxy
            del req.headers['Ytdl-request-proxy']

        if proxy == '__noproxy__':
            return None  # No Proxy
        return compat_urllib_request.ProxyHandler.proxy_open(
            self, req, proxy, type)
