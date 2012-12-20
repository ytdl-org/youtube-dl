#!/usr/bin/env python

import os
import socket
import sys
import unittest

# Allow direct execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youtube_dl.FileDownloader
import youtube_dl.InfoExtractors
from youtube_dl.utils import *

PARAMETERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parameters.json")

# General configuration (from __init__, not very elegant...)
jar = compat_cookiejar.CookieJar()
cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
proxy_handler = compat_urllib_request.ProxyHandler()
opener = compat_urllib_request.build_opener(proxy_handler, cookie_processor, YoutubeDLHandler())
compat_urllib_request.install_opener(opener)
socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

class FileDownloader(youtube_dl.FileDownloader):
    def __init__(self, *args, **kwargs):
        youtube_dl.FileDownloader.__init__(self, *args, **kwargs)
        self.to_stderr = self.to_screen

with io.open(PARAMETERS_FILE, encoding='utf-8') as pf:
    params = json.load(pf)
params['writeinfojson'] = True
params['skip_download'] = True

TEST_ID = 'BaW_jenozKc'
INFO_JSON_FILE = TEST_ID + '.mp4.info.json'

class TestInfoJSON(unittest.TestCase):
    def setUp(self):
        # Clear old files
        self.tearDown()

    def test_info_json(self):
        ie = youtube_dl.InfoExtractors.YoutubeIE()
        fd = FileDownloader(params)
        fd.add_info_extractor(ie)
        fd.download([TEST_ID])
        self.assertTrue(os.path.exists(INFO_JSON_FILE))

    def tearDown(self):
        if os.path.exists(INFO_JSON_FILE):
            os.remove(INFO_JSON_FILE)

if __name__ == '__main__':
    unittest.main()
