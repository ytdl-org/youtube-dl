#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import re
import sys
import subprocess
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import (
    FakeLogger,
    FakeYDL,
    http_server_port,
    try_rm,
)
from youtube_dl import YoutubeDL
from youtube_dl.compat import (
    compat_contextlib_suppress,
    compat_http_cookiejar_Cookie,
    compat_http_server,
    compat_kwargs,
)
from youtube_dl.utils import (
    encodeFilename,
    join_nonempty,
)
from youtube_dl.downloader.external import (
    Aria2cFD,
    Aria2pFD,
    AxelFD,
    CurlFD,
    FFmpegFD,
    HttpieFD,
    WgetFD,
)
from youtube_dl.postprocessor import (
    FFmpegPostProcessor,
)
import threading

TEST_SIZE = 10 * 1024

TEST_COOKIE = {
    'version': 0,
    'name': 'test',
    'value': 'ytdlp',
    'port': None,
    'port_specified': False,
    'domain': '.example.com',
    'domain_specified': True,
    'domain_initial_dot': False,
    'path': '/',
    'path_specified': True,
    'secure': False,
    'expires': None,
    'discard': False,
    'comment': None,
    'comment_url': None,
    'rest': {},
}

TEST_COOKIE_VALUE = join_nonempty('name', 'value', delim='=', from_dict=TEST_COOKIE)

TEST_INFO = {'url': 'http://www.example.com/'}


def cookiejar_Cookie(**cookie_args):
    return compat_http_cookiejar_Cookie(**compat_kwargs(cookie_args))


def ifExternalFDAvailable(externalFD):
    return unittest.skipUnless(externalFD.available(),
                               externalFD.get_basename() + ' not found')


class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_content_range(self, total=None):
        range_header = self.headers.get('Range')
        start = end = None
        if range_header:
            mobj = re.match(r'bytes=(\d+)-(\d+)', range_header)
            if mobj:
                start, end = (int(mobj.group(i)) for i in (1, 2))
        valid_range = start is not None and end is not None
        if valid_range:
            content_range = 'bytes %d-%d' % (start, end)
            if total:
                content_range += '/%d' % total
            self.send_header('Content-Range', content_range)
        return (end - start + 1) if valid_range else total

    def serve(self, range=True, content_length=True):
        self.send_response(200)
        self.send_header('Content-Type', 'video/mp4')
        size = TEST_SIZE
        if range:
            size = self.send_content_range(TEST_SIZE)
        if content_length:
            self.send_header('Content-Length', size)
        self.end_headers()
        self.wfile.write(b'#' * size)

    def do_GET(self):
        if self.path == '/regular':
            self.serve()
        elif self.path == '/no-content-length':
            self.serve(content_length=False)
        elif self.path == '/no-range':
            self.serve(range=False)
        elif self.path == '/no-range-no-content-length':
            self.serve(range=False, content_length=False)
        else:
            assert False, 'unrecognised server path'


@ifExternalFDAvailable(Aria2pFD)
class TestAria2pFD(unittest.TestCase):
    def setUp(self):
        self.httpd = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), HTTPTestRequestHandler)
        self.port = http_server_port(self.httpd)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def download(self, params, ep):
        with subprocess.Popen(
            ['aria2c', '--enable-rpc'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) as process:
            if not process.poll():
                filename = 'testfile.mp4'
                params['logger'] = FakeLogger()
                params['outtmpl'] = filename
                ydl = YoutubeDL(params)
                try_rm(encodeFilename(filename))
                self.assertEqual(ydl.download(['http://127.0.0.1:%d/%s' % (self.port, ep)]), 0)
                self.assertEqual(os.path.getsize(encodeFilename(filename)), TEST_SIZE)
                try_rm(encodeFilename(filename))
            process.kill()

    def download_all(self, params):
        for ep in ('regular', 'no-content-length', 'no-range', 'no-range-no-content-length'):
            self.download(params, ep)

    def test_regular(self):
        self.download_all({'external_downloader': 'aria2p'})

    def test_chunked(self):
        self.download_all({
            'external_downloader': 'aria2p',
            'http_chunk_size': 1000,
        })


@ifExternalFDAvailable(HttpieFD)
class TestHttpieFD(unittest.TestCase):
    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = HttpieFD(ydl, {})
            self.assertEqual(
                downloader._make_cmd('test', TEST_INFO),
                ['http', '--download', '--output', 'test', 'http://www.example.com/'])

            # Test cookie header is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            self.assertEqual(
                downloader._make_cmd('test', TEST_INFO),
                ['http', '--download', '--output', 'test',
                 'http://www.example.com/', 'Cookie:' + TEST_COOKIE_VALUE])


@ifExternalFDAvailable(AxelFD)
class TestAxelFD(unittest.TestCase):
    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = AxelFD(ydl, {})
            self.assertEqual(
                downloader._make_cmd('test', TEST_INFO),
                ['axel', '-o', 'test', '--', 'http://www.example.com/'])

            # Test cookie header is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            self.assertEqual(
                downloader._make_cmd('test', TEST_INFO),
                ['axel', '-o', 'test', '-H', 'Cookie: ' + TEST_COOKIE_VALUE,
                 '--max-redirect=0', '--', 'http://www.example.com/'])


@ifExternalFDAvailable(WgetFD)
class TestWgetFD(unittest.TestCase):
    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = WgetFD(ydl, {})
            self.assertNotIn('--load-cookies', downloader._make_cmd('test', TEST_INFO))
            # Test cookiejar tempfile arg is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            self.assertIn('--load-cookies', downloader._make_cmd('test', TEST_INFO))


@ifExternalFDAvailable(CurlFD)
class TestCurlFD(unittest.TestCase):
    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = CurlFD(ydl, {})
            self.assertNotIn('--cookie', downloader._make_cmd('test', TEST_INFO))
            # Test cookie header is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            self.assertIn('--cookie', downloader._make_cmd('test', TEST_INFO))
            self.assertIn(TEST_COOKIE_VALUE, downloader._make_cmd('test', TEST_INFO))


@ifExternalFDAvailable(Aria2cFD)
class TestAria2cFD(unittest.TestCase):
    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = Aria2cFD(ydl, {})
            downloader._make_cmd('test', TEST_INFO)
            self.assertFalse(hasattr(downloader, '_cookies_tempfile'))

            # Test cookiejar tempfile arg is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            cmd = downloader._make_cmd('test', TEST_INFO)
            self.assertIn('--load-cookies=%s' % downloader._cookies_tempfile, cmd)


# Handle delegated availability
def ifFFmpegFDAvailable(externalFD):
    # raise SkipTest, or set False!
    avail = ifExternalFDAvailable(externalFD) and False
    with compat_contextlib_suppress(Exception):
        avail = FFmpegPostProcessor(downloader=None).available
    return unittest.skipUnless(
        avail, externalFD.get_basename() + ' not found')


@ifFFmpegFDAvailable(FFmpegFD)
class TestFFmpegFD(unittest.TestCase):
    _args = []

    def _test_cmd(self, args):
        self._args = args

    def test_make_cmd(self):
        with FakeYDL() as ydl:
            downloader = FFmpegFD(ydl, {})
            downloader._debug_cmd = self._test_cmd
            info_dict = TEST_INFO.copy()
            info_dict['ext'] = 'mp4'

            downloader._call_downloader('test', info_dict)
            self.assertEqual(self._args, [
                'ffmpeg', '-y', '-i', 'http://www.example.com/',
                '-c', 'copy', '-f', 'mp4', 'file:test'])

            # Test cookies arg is added
            ydl.cookiejar.set_cookie(cookiejar_Cookie(**TEST_COOKIE))
            downloader._call_downloader('test', info_dict)
            self.assertEqual(self._args, [
                'ffmpeg', '-y', '-cookies', TEST_COOKIE_VALUE + '; path=/; domain=.example.com;\r\n',
                '-i', 'http://www.example.com/', '-c', 'copy', '-f', 'mp4', 'file:test'])


if __name__ == '__main__':
    unittest.main()
