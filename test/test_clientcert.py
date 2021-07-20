#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import http_server_port
from youtube_dl import YoutubeDL
from youtube_dl.compat import compat_http_server
import ssl
import threading

from test.test_http import HTTPTestRequestHandler, FakeLogger


# See https://gist.github.com/dergachev/7028596
# and http://www.piware.de/2011/01/creating-an-https-server-in-python/
# and https://blog.devolutions.net/2020/07/tutorial-how-to-generate-secure-self-signed-server-and-client-certificates-with-openssl


TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class TestClientCert(unittest.TestCase):
    def setUp(self):
        certfn = os.path.join(TEST_DIR, 'testcert.pem')
        cacertfn = os.path.join(TEST_DIR, 'testdata', 'clientcert', 'ca.crt')
        self.httpd = compat_http_server.HTTPServer(('127.0.0.1', 0), HTTPTestRequestHandler)
        self.httpd.socket = ssl.wrap_socket(
            self.httpd.socket, cert_reqs=ssl.CERT_REQUIRED, ca_certs=cacertfn, certfile=certfn, server_side=True)
        self.port = http_server_port(self.httpd)
        self.server_thread = threading.Thread(target=self.httpd.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def test_check_clientcertificate(self):
        clientcertfn = os.path.join(TEST_DIR, 'testdata', 'clientcert', 'client.crt')
        ydl = YoutubeDL({'logger': FakeLogger(), 'clientcertificate': clientcertfn,
            # Disable client-side validation of unacceptable self-signed testcert.pem
            # The test is of a check on the server side, so unaffected
            'nocheckcertificate': True,
            })
        r = ydl.extract_info('https://127.0.0.1:%d/video.html' % self.port)
        self.assertEqual(r['entries'][0]['url'], 'https://127.0.0.1:%d/vid.mp4' % self.port)


if __name__ == '__main__':
    unittest.main()
