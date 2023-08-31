#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import contextlib
import gzip
import io
import ssl
import tempfile
import threading
import zlib

# avoid deprecated alias assertRaisesRegexp
if hasattr(unittest.TestCase, 'assertRaisesRegex'):
    unittest.TestCase.assertRaisesRegexp = unittest.TestCase.assertRaisesRegex

try:
    import brotli
except ImportError:
    brotli = None
try:
    from urllib.request import pathname2url
except ImportError:
    from urllib import pathname2url

from youtube_dl.compat import (
    compat_http_cookiejar_Cookie,
    compat_http_server,
    compat_str as str,
    compat_urllib_error,
    compat_urllib_HTTPError,
    compat_urllib_parse,
    compat_urllib_request,
)

from youtube_dl.utils import (
    sanitized_Request,
    update_Request,
    urlencode_postdata,
)

from test.helper import (
    expectedFailureIf,
    FakeYDL,
    FakeLogger,
    http_server_port,
)
from youtube_dl import YoutubeDL

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    # work-around old/new -style class inheritance
    def super(self, meth_name, *args, **kwargs):
        from types import MethodType
        try:
            super()
            fn = lambda s, m, *a, **k: getattr(super(), m)(*a, **k)
        except TypeError:
            fn = lambda s, m, *a, **k: getattr(compat_http_server.BaseHTTPRequestHandler, m)(s, *a, **k)
        self.super = MethodType(fn, self)
        return self.super(meth_name, *args, **kwargs)

    def log_message(self, format, *args):
        pass

    def _headers(self):
        payload = str(self.headers).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self):
        self.send_response(int(self.path[len('/redirect_'):]))
        self.send_header('Location', '/method')
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _method(self, method, payload=None):
        self.send_response(200)
        self.send_header('Content-Length', str(len(payload or '')))
        self.send_header('Method', method)
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def _status(self, status):
        payload = '<html>{0} NOT FOUND</html>'.format(status).encode('utf-8')
        self.send_response(int(status))
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_data(self):
        if 'Content-Length' in self.headers:
            return self.rfile.read(int(self.headers['Content-Length']))

    def _test_url(self, path, host='127.0.0.1', scheme='http', port=None):
        return '{0}://{1}:{2}/{3}'.format(
            scheme, host,
            port if port is not None
            else http_server_port(self.server), path)

    def do_POST(self):
        data = self._read_data()
        if self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('POST', data)
        elif self.path.startswith('/headers'):
            self._headers()
        else:
            self._status(404)

    def do_HEAD(self):
        if self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('HEAD')
        else:
            self._status(404)

    def do_PUT(self):
        data = self._read_data()
        if self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('PUT', data)
        else:
            self._status(404)

    def do_GET(self):

        def respond(payload=b'<html><video src="/vid.mp4" /></html>',
                    payload_type='text/html; charset=utf-8',
                    payload_encoding=None,
                    resp_code=200):
            self.send_response(resp_code)
            self.send_header('Content-Type', payload_type)
            if payload_encoding:
                self.send_header('Content-Encoding', payload_encoding)
            self.send_header('Content-Length', str(len(payload)))  # required for persistent connections
            self.end_headers()
            self.wfile.write(payload)

        def gzip_compress(p):
            buf = io.BytesIO()
            with contextlib.closing(gzip.GzipFile(fileobj=buf, mode='wb')) as f:
                f.write(p)
            return buf.getvalue()

        if self.path == '/video.html':
            respond()
        elif self.path == '/vid.mp4':
            respond(b'\x00\x00\x00\x00\x20\x66\x74[video]', 'video/mp4')
        elif self.path == '/302':
            if sys.version_info[0] == 3:
                # XXX: Python 3 http server does not allow non-ASCII header values
                self.send_response(404)
                self.end_headers()
                return

            new_url = self._test_url('中文.html')
            self.send_response(302)
            self.send_header(b'Location', new_url.encode('utf-8'))
            self.end_headers()
        elif self.path == '/%E4%B8%AD%E6%96%87.html':
            respond()
        elif self.path == '/%c7%9f':
            respond()
        elif self.path == '/redirect_dotsegments':
            self.send_response(301)
            # redirect to /headers but with dot segments before
            self.send_header('Location', '/a/b/./../../headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path.startswith('/redirect_'):
            self._redirect()
        elif self.path.startswith('/method'):
            self._method('GET')
        elif self.path.startswith('/headers'):
            self._headers()
        elif self.path.startswith('/308-to-headers'):
            self.send_response(308)
            self.send_header('Location', '/headers')
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/trailing_garbage':
            payload = b'<html><video src="/vid.mp4" /></html>'
            compressed = gzip_compress(payload) + b'trailing garbage'
            respond(compressed, payload_encoding='gzip')
        elif self.path == '/302-non-ascii-redirect':
            new_url = self._test_url('中文.html')
            # actually respond with permanent redirect
            self.send_response(301)
            self.send_header('Location', new_url)
            self.send_header('Content-Length', '0')
            self.end_headers()
        elif self.path == '/content-encoding':
            encodings = self.headers.get('ytdl-encoding', '')
            payload = b'<html><video src="/vid.mp4" /></html>'
            for encoding in filter(None, (e.strip() for e in encodings.split(','))):
                if encoding == 'br' and brotli:
                    payload = brotli.compress(payload)
                elif encoding == 'gzip':
                    payload = gzip_compress(payload)
                elif encoding == 'deflate':
                    payload = zlib.compress(payload)
                elif encoding == 'unsupported':
                    payload = b'raw'
                    break
                else:
                    self._status(415)
                    return
            respond(payload, payload_encoding=encodings)

        else:
            self._status(404)

    def send_header(self, keyword, value):
        """
        Forcibly allow HTTP server to send non percent-encoded non-ASCII characters in headers.
        This is against what is defined in RFC 3986: but we need to test that we support this
        since some sites incorrectly do this.
        """
        if keyword.lower() == 'connection':
            return self.super('send_header', keyword, value)

        if not hasattr(self, '_headers_buffer'):
            self._headers_buffer = []

        self._headers_buffer.append('{0}: {1}\r\n'.format(keyword, value).encode('utf-8'))

    def end_headers(self):
        if hasattr(self, '_headers_buffer'):
            self.wfile.write(b''.join(self._headers_buffer))
            self._headers_buffer = []
        self.super('end_headers')


class TestHTTP(unittest.TestCase):
    # when does it make sense to check the SSL certificate?
    _check_cert = (
        sys.version_info >= (3, 2)
        or (sys.version_info[0] == 2 and sys.version_info[1:] >= (7, 19)))

    def setUp(self):
        # HTTP server
        self.http_httpd = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), HTTPTestRequestHandler)
        self.http_port = http_server_port(self.http_httpd)

        self.http_server_thread = threading.Thread(target=self.http_httpd.serve_forever)
        self.http_server_thread.daemon = True
        self.http_server_thread.start()

        try:
            from http.server import ThreadingHTTPServer
        except ImportError:
            try:
                from socketserver import ThreadingMixIn
            except ImportError:
                from SocketServer import ThreadingMixIn

            class ThreadingHTTPServer(ThreadingMixIn, compat_http_server.HTTPServer):
                pass

        # HTTPS server
        certfn = os.path.join(TEST_DIR, 'testcert.pem')
        self.https_httpd = ThreadingHTTPServer(
            ('127.0.0.1', 0), HTTPTestRequestHandler)
        try:
            sslctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
            sslctx.verify_mode = ssl.CERT_NONE
            sslctx.check_hostname = False
            sslctx.load_cert_chain(certfn, None)
            self.https_httpd.socket = sslctx.wrap_socket(
                self.https_httpd.socket, server_side=True)
        except AttributeError:
            self.https_httpd.socket = ssl.wrap_socket(
                self.https_httpd.socket, certfile=certfn, server_side=True)

        self.https_port = http_server_port(self.https_httpd)
        self.https_server_thread = threading.Thread(target=self.https_httpd.serve_forever)
        self.https_server_thread.daemon = True
        self.https_server_thread.start()

    def tearDown(self):

        def closer(svr):
            def _closer():
                svr.shutdown()
                svr.server_close()
            return _closer

        shutdown_thread = threading.Thread(target=closer(self.http_httpd))
        shutdown_thread.start()
        self.http_server_thread.join(2.0)

        shutdown_thread = threading.Thread(target=closer(self.https_httpd))
        shutdown_thread.start()
        self.https_server_thread.join(2.0)

    def _test_url(self, path, host='127.0.0.1', scheme='http', port=None):
        return '{0}://{1}:{2}/{3}'.format(
            scheme, host,
            port if port is not None
            else self.https_port if scheme == 'https'
            else self.http_port, path)

    @unittest.skipUnless(_check_cert, 'No support for certificate check in SSL')
    def test_nocheckcertificate(self):
        with FakeYDL({'logger': FakeLogger()}) as ydl:
            with self.assertRaises(compat_urllib_error.URLError):
                ydl.urlopen(sanitized_Request(self._test_url('headers', scheme='https')))

        with FakeYDL({'logger': FakeLogger(), 'nocheckcertificate': True}) as ydl:
            r = ydl.urlopen(sanitized_Request(self._test_url('headers', scheme='https')))
            self.assertEqual(r.getcode(), 200)
            r.close()

    def test_percent_encode(self):
        with FakeYDL() as ydl:
            # Unicode characters should be encoded with uppercase percent-encoding
            res = ydl.urlopen(sanitized_Request(self._test_url('中文.html')))
            self.assertEqual(res.getcode(), 200)
            res.close()
            # don't normalize existing percent encodings
            res = ydl.urlopen(sanitized_Request(self._test_url('%c7%9f')))
            self.assertEqual(res.getcode(), 200)
            res.close()

    def test_unicode_path_redirection(self):
        with FakeYDL() as ydl:
            r = ydl.urlopen(sanitized_Request(self._test_url('302-non-ascii-redirect')))
            self.assertEqual(r.url, self._test_url('%E4%B8%AD%E6%96%87.html'))
            r.close()

    def test_redirect(self):
        with FakeYDL() as ydl:
            def do_req(redirect_status, method, check_no_content=False):
                data = b'testdata' if method in ('POST', 'PUT') else None
                res = ydl.urlopen(sanitized_Request(
                    self._test_url('redirect_{0}'.format(redirect_status)),
                    method=method, data=data))
                if check_no_content:
                    self.assertNotIn('Content-Type', res.headers)
                return res.read().decode('utf-8'), res.headers.get('method', '')
            # A 303 must either use GET or HEAD for subsequent request
            self.assertEqual(do_req(303, 'POST'), ('', 'GET'))
            self.assertEqual(do_req(303, 'HEAD'), ('', 'HEAD'))

            self.assertEqual(do_req(303, 'PUT'), ('', 'GET'))

            # 301 and 302 turn POST only into a GET, with no Content-Type
            self.assertEqual(do_req(301, 'POST', True), ('', 'GET'))
            self.assertEqual(do_req(301, 'HEAD'), ('', 'HEAD'))
            self.assertEqual(do_req(302, 'POST', True), ('', 'GET'))
            self.assertEqual(do_req(302, 'HEAD'), ('', 'HEAD'))

            self.assertEqual(do_req(301, 'PUT'), ('testdata', 'PUT'))
            self.assertEqual(do_req(302, 'PUT'), ('testdata', 'PUT'))

            # 307 and 308 should not change method
            for m in ('POST', 'PUT'):
                self.assertEqual(do_req(307, m), ('testdata', m))
                self.assertEqual(do_req(308, m), ('testdata', m))

            self.assertEqual(do_req(307, 'HEAD'), ('', 'HEAD'))
            self.assertEqual(do_req(308, 'HEAD'), ('', 'HEAD'))

            # These should not redirect and instead raise an HTTPError
            for code in (300, 304, 305, 306):
                with self.assertRaises(compat_urllib_HTTPError):
                    do_req(code, 'GET')

    # Jython 2.7.1 times out for some reason
    @expectedFailureIf(sys.platform.startswith('java') and sys.version_info < (2, 7, 2))
    def test_content_type(self):
        # https://github.com/yt-dlp/yt-dlp/commit/379a4f161d4ad3e40932dcf5aca6e6fb9715ab28
        with FakeYDL({'nocheckcertificate': True}) as ydl:
            # method should be auto-detected as POST
            r = sanitized_Request(self._test_url('headers', scheme='https'), data=urlencode_postdata({'test': 'test'}))

            headers = ydl.urlopen(r).read().decode('utf-8')
            self.assertIn('Content-Type: application/x-www-form-urlencoded', headers)

            # test http
            r = sanitized_Request(self._test_url('headers'), data=urlencode_postdata({'test': 'test'}))
            headers = ydl.urlopen(r).read().decode('utf-8')
            self.assertIn('Content-Type: application/x-www-form-urlencoded', headers)

    def test_update_req(self):
        req = sanitized_Request('http://example.com')
        assert req.data is None
        assert req.get_method() == 'GET'
        assert not req.has_header('Content-Type')
        # Test that zero-byte payloads will be sent
        req = update_Request(req, data=b'')
        assert req.data == b''
        assert req.get_method() == 'POST'
        # yt-dl expects data to be encoded and Content-Type to be added by sender
        # assert req.get_header('Content-Type') == 'application/x-www-form-urlencoded'

    def test_cookiejar(self):
        with FakeYDL() as ydl:
            ydl.cookiejar.set_cookie(compat_http_cookiejar_Cookie(
                0, 'test', 'ytdl', None, False, '127.0.0.1', True,
                False, '/headers', True, False, None, False, None, None, {}))
            data = ydl.urlopen(sanitized_Request(
                self._test_url('headers'))).read().decode('utf-8')
            self.assertIn('Cookie: test=ytdl', data)

    def test_passed_cookie_header(self):
        # We should accept a Cookie header being passed as in normal headers and handle it appropriately.
        with FakeYDL() as ydl:
            # Specified Cookie header should be used
            res = ydl.urlopen(sanitized_Request(
                self._test_url('headers'), headers={'Cookie': 'test=test'})).read().decode('utf-8')
            self.assertIn('Cookie: test=test', res)

            # Specified Cookie header should be removed on any redirect
            res = ydl.urlopen(sanitized_Request(
                self._test_url('308-to-headers'), headers={'Cookie': 'test=test'})).read().decode('utf-8')
            self.assertNotIn('Cookie: test=test', res)

            # Specified Cookie header should override global cookiejar for that request
            ydl.cookiejar.set_cookie(compat_http_cookiejar_Cookie(
                0, 'test', 'ytdlp', None, False, '127.0.0.1', True,
                False, '/headers', True, False, None, False, None, None, {}))
            data = ydl.urlopen(sanitized_Request(
                self._test_url('headers'), headers={'Cookie': 'test=test'})).read().decode('utf-8')
            self.assertNotIn('Cookie: test=ytdlp', data)
            self.assertIn('Cookie: test=test', data)

    def test_no_compression_compat_header(self):
        with FakeYDL() as ydl:
            data = ydl.urlopen(
                sanitized_Request(
                    self._test_url('headers'),
                    headers={'Youtubedl-no-compression': True})).read()
            self.assertIn(b'Accept-Encoding: identity', data)
            self.assertNotIn(b'youtubedl-no-compression', data.lower())

    def test_gzip_trailing_garbage(self):
        # https://github.com/ytdl-org/youtube-dl/commit/aa3e950764337ef9800c936f4de89b31c00dfcf5
        # https://github.com/ytdl-org/youtube-dl/commit/6f2ec15cee79d35dba065677cad9da7491ec6e6f
        with FakeYDL() as ydl:
            data = ydl.urlopen(sanitized_Request(self._test_url('trailing_garbage'))).read().decode('utf-8')
            self.assertEqual(data, '<html><video src="/vid.mp4" /></html>')

    def __test_compression(self, encoding):
        with FakeYDL() as ydl:
            res = ydl.urlopen(
                sanitized_Request(
                    self._test_url('content-encoding'),
                    headers={'ytdl-encoding': encoding}))
            # decoded encodings are removed: only check for valid decompressed data
            self.assertEqual(res.read(), b'<html><video src="/vid.mp4" /></html>')

    @unittest.skipUnless(brotli, 'brotli support is not installed')
    def test_brotli(self):
        self.__test_compression('br')

    def test_deflate(self):
        self.__test_compression('deflate')

    def test_gzip(self):
        self.__test_compression('gzip')

    def test_multiple_encodings(self):
        # https://www.rfc-editor.org/rfc/rfc9110.html#section-8.4
        for pair in ('gzip,deflate', 'deflate, gzip', 'gzip, gzip', 'deflate, deflate'):
            self.__test_compression(pair)

    def test_unsupported_encoding(self):
        # it should return the raw content
        with FakeYDL() as ydl:
            res = ydl.urlopen(
                sanitized_Request(
                    self._test_url('content-encoding'),
                    headers={'ytdl-encoding': 'unsupported'}))
            self.assertEqual(res.headers.get('Content-Encoding'), 'unsupported')
            self.assertEqual(res.read(), b'raw')

    def test_remove_dot_segments(self):
        with FakeYDL() as ydl:
            res = ydl.urlopen(sanitized_Request(self._test_url('a/b/./../../headers')))
            self.assertEqual(compat_urllib_parse.urlparse(res.geturl()).path, '/headers')

            res = ydl.urlopen(sanitized_Request(self._test_url('redirect_dotsegments')))
            self.assertEqual(compat_urllib_parse.urlparse(res.geturl()).path, '/headers')


def _build_proxy_handler(name):
    class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
        proxy_name = name

        def log_message(self, format, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write('{0}: {1}'.format(self.proxy_name, self.path).encode('utf-8'))
    return HTTPTestRequestHandler


class TestProxy(unittest.TestCase):
    def setUp(self):
        self.proxy = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), _build_proxy_handler('normal'))
        self.port = http_server_port(self.proxy)
        self.proxy_thread = threading.Thread(target=self.proxy.serve_forever)
        self.proxy_thread.daemon = True
        self.proxy_thread.start()

        self.geo_proxy = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), _build_proxy_handler('geo'))
        self.geo_port = http_server_port(self.geo_proxy)
        self.geo_proxy_thread = threading.Thread(target=self.geo_proxy.serve_forever)
        self.geo_proxy_thread.daemon = True
        self.geo_proxy_thread.start()

    def tearDown(self):

        def closer(svr):
            def _closer():
                svr.shutdown()
                svr.server_close()
            return _closer

        shutdown_thread = threading.Thread(target=closer(self.proxy))
        shutdown_thread.start()
        self.proxy_thread.join(2.0)

        shutdown_thread = threading.Thread(target=closer(self.geo_proxy))
        shutdown_thread.start()
        self.geo_proxy_thread.join(2.0)

    def _test_proxy(self, host='127.0.0.1', port=None):
        return '{0}:{1}'.format(
            host, port if port is not None else self.port)

    def test_proxy(self):
        geo_proxy = self._test_proxy(port=self.geo_port)
        ydl = YoutubeDL({
            'proxy': self._test_proxy(),
            'geo_verification_proxy': geo_proxy,
        })
        url = 'http://foo.com/bar'
        response = ydl.urlopen(url).read().decode('utf-8')
        self.assertEqual(response, 'normal: {0}'.format(url))

        req = compat_urllib_request.Request(url)
        req.add_header('Ytdl-request-proxy', geo_proxy)
        response = ydl.urlopen(req).read().decode('utf-8')
        self.assertEqual(response, 'geo: {0}'.format(url))

    def test_proxy_with_idn(self):
        ydl = YoutubeDL({
            'proxy': self._test_proxy(),
        })
        url = 'http://中文.tw/'
        response = ydl.urlopen(url).read().decode('utf-8')
        # b'xn--fiq228c' is '中文'.encode('idna')
        self.assertEqual(response, 'normal: http://xn--fiq228c.tw/')


class TestFileURL(unittest.TestCase):
    # See https://github.com/ytdl-org/youtube-dl/issues/8227
    def test_file_urls(self):
        tf = tempfile.NamedTemporaryFile(delete=False)
        tf.write(b'foobar')
        tf.close()
        url = compat_urllib_parse.urljoin('file://', pathname2url(tf.name))
        with FakeYDL() as ydl:
            self.assertRaisesRegexp(
                compat_urllib_error.URLError, 'file:// scheme is explicitly disabled in youtube-dl for security reasons', ydl.urlopen, url)
        # not yet implemented
        """
        with FakeYDL({'enable_file_urls': True}) as ydl:
            res = ydl.urlopen(url)
            self.assertEqual(res.read(), b'foobar')
            res.close()
        """
        os.unlink(tf.name)


if __name__ == '__main__':
    unittest.main()
