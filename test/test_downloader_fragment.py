#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeLogger, http_server_port
from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
from youtube_dl.downloader.dash import DashSegmentsFD


FRAGMENTS = (b'first segment', b'second segment')


class FragmentRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        content = FRAGMENTS[int(self.path[1:])]
        self.send_response(200)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)


class TestFragmentFD(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.filename = os.path.join(self.directory, 'video.mp4')
        self.httpd = compat_http_server.HTTPServer(
            ('127.0.0.1', 0), FragmentRequestHandler)
        self.httpd.requests = []
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.server_thread.join()
        self.httpd.server_close()
        shutil.rmtree(self.directory)

    def prepare_partial(self, state):
        with open(self.filename + '.part', 'wb') as stream:
            stream.write(FRAGMENTS[0])
        if state is not None:
            with open(self.filename + '.ytdl', 'w') as stream:
                stream.write(state)

    def download(self, continuedl=True):
        params = {'continuedl': continuedl, 'logger': FakeLogger()}
        downloader = DashSegmentsFD(YoutubeDL(params), params)
        self.assertTrue(downloader.real_download(self.filename, {
            'fragments': [
                {'url': 'http://127.0.0.1:%d/%d' % (
                    http_server_port(self.httpd), index)}
                for index in range(len(FRAGMENTS))],
        }))
        with open(self.filename, 'rb') as stream:
            self.assertEqual(stream.read(), b''.join(FRAGMENTS))
        self.assertFalse(os.path.exists(self.filename + '.part'))
        self.assertFalse(os.path.exists(self.filename + '.ytdl'))

    def test_fresh_download(self):
        self.download()
        self.assertEqual(self.httpd.requests, ['/0', '/1'])

    def test_resume(self):
        self.prepare_partial(json.dumps({
            'downloader': {'current_fragment': {'index': 1}}}))
        self.download()
        self.assertEqual(self.httpd.requests, ['/1'])

    def test_no_continue(self):
        self.prepare_partial(json.dumps({
            'downloader': {'current_fragment': {'index': 1}}}))
        self.download(continuedl=False)
        self.assertEqual(self.httpd.requests, ['/0', '/1'])

    def test_no_continue_without_state(self):
        self.prepare_partial(None)
        self.download(continuedl=False)
        self.assertEqual(self.httpd.requests, ['/0', '/1'])

    def test_corrupt_state(self):
        self.prepare_partial('{')
        self.download()
        self.assertEqual(self.httpd.requests, ['/0', '/1'])


if __name__ == '__main__':
    unittest.main()
