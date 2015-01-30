#!/usr/bin/env python
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
import ssl
import threading

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class HTTPTestRequestHandler(compat_http_server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/video.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'<html><video src="/vid.mp4" /></html>')
        elif self.path == '/vid.mp4':
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.end_headers()
            self.wfile.write(b'\x00\x00\x00\x00\x20\x66\x74[video]')
        else:
            assert False


class FakeLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


class TestHTTP(unittest.TestCase):
    def setUp(self):
        certfn = os.path.join(TEST_DIR, 'testcert.pem')
        self.httpd = compat_http_server.HTTPServer(
            ('localhost', 0), HTTPTestRequestHandler)
        self.httpd.socket = ssl.wrap_socket(
            self.httpd.socket, certfile=certfn, server_side=True)
        self.port = self.httpd.socket.getsockname()[1]
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def test_nocheckcertificate(self):
        if sys.version_info >= (2, 7, 9):  # No certificate checking anyways
            ydl = YoutubeDL({'logger': FakeLogger()})
            self.assertRaises(
                Exception,
                ydl.extract_info, 'https://localhost:%d/video.html' % self.port)

        ydl = YoutubeDL({'logger': FakeLogger(), 'nocheckcertificate': True})
        r = ydl.extract_info('https://localhost:%d/video.html' % self.port)
        self.assertEqual(r['url'], 'https://localhost:%d/vid.mp4' % self.port)

if __name__ == '__main__':
    unittest.main()
