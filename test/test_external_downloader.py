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
    http_server_port,
    try_rm,
)
from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
from youtube_dl.utils import encodeFilename
from youtube_dl.downloader.external import Aria2pFD
import threading

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


TEST_SIZE = 10 * 1024


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


@unittest.skipUnless(Aria2pFD.available(), 'aria2p module not found')
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


if __name__ == '__main__':
    unittest.main()
