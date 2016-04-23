#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import (FakeYDL, get_params)
from youtube_dl.compat import compat_urllib_request


class TestSocks(unittest.TestCase):
    @staticmethod
    def _check_params(attrs):
        params = get_params()
        for attr in attrs:
            if attr not in params:
                print('Missing %s. Skipping.' % attr)
                return
        return params

    def test_proxy_http(self):
        params = self._check_params(['primary_proxy', 'primary_server_ip'])
        if params is None:
            return
        ydl = FakeYDL({
            'proxy': params['primary_proxy']
        })
        self.assertEqual(
            ydl.urlopen('http://yt-dl.org/ip').read().decode('utf-8'),
            params['primary_server_ip'])

    def test_proxy_https(self):
        params = self._check_params(['primary_proxy', 'primary_server_ip'])
        if params is None:
            return
        ydl = FakeYDL({
            'proxy': params['primary_proxy']
        })
        self.assertEqual(
            ydl.urlopen('https://yt-dl.org/ip').read().decode('utf-8'),
            params['primary_server_ip'])

    def test_secondary_proxy_http(self):
        params = self._check_params(['secondary_proxy', 'secondary_server_ip'])
        if params is None:
            return
        ydl = FakeYDL()
        req = compat_urllib_request.Request('http://yt-dl.org/ip')
        req.add_header('Ytdl-request-proxy', params['secondary_proxy'])
        self.assertEqual(
            ydl.urlopen(req).read().decode('utf-8'),
            params['secondary_server_ip'])

    def test_secondary_proxy_https(self):
        params = self._check_params(['secondary_proxy', 'secondary_server_ip'])
        if params is None:
            return
        ydl = FakeYDL()
        req = compat_urllib_request.Request('https://yt-dl.org/ip')
        req.add_header('Ytdl-request-proxy', params['secondary_proxy'])
        self.assertEqual(
            ydl.urlopen(req).read().decode('utf-8'),
            params['secondary_server_ip'])


if __name__ == '__main__':
    unittest.main()
