#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test.helper import FakeYDL
from youtube_dl.extractor import NiconicoIE
from unittest import TestCase

class NiconicoIEWithCredentialsFail(NiconicoIE):
    def _get_login_info(self):
        return 'fake', 'fake'

class NiconicoIEWithCredentials(NiconicoIE):
    def _get_login_info(self):
        return 'juliaz199701@gmail.com', '12345zyx'


class WarningLogger(object):
    def __init__(self):
        self.messages = []

    def warning(self, msg):
        self.messages.append(msg)

    def debug(self, msg):
        pass

    def error(self, msg):
        pass



class TestNiconicoSDKInterpreter(unittest.TestCase):

    def test_login(self):
        '''
        Test the functionality of NiconicoSDKInterpreter by trying to log in

        If `sign` is incorrect, /validate call throws an HTTP 556 error
        '''
        logger = WarningLogger()
        iefail = NiconicoIEWithCredentialsFail(FakeYDL({'logger': logger}))
        res = iefail._login()
        self.assertTrue('unable to log in:' in logger.messages[0])

        ie = NiconicoIEWithCredentials(FakeYDL())
        res = ie._login()
        self.assertTrue(res)

    def test_extract(self):
        ie = NiconicoIEWithCredentials(FakeYDL())
        ie._login()
        actual_dict = ie._real_extract('http://www.nicovideo.jp/watch/sm18238488')
        expected_dict = {'id': 'sm18238488',
                'title': '【実写版】ミュータントタートルズ',
                'formats': [{'url': 'http://smile-ccm11.nicovideo.jp/smile?m=18238488.31558',
                             'ext': 'mp4', 'format_id': 'normal'}],
                'thumbnail': 'http://nicovideo.cdn.nimg.jp/thumbnails/18238488/18238488',
                'description': '昔のＶＨＳを整理していたら出てきました。',
                'uploader': 'may iluma',
                'timestamp': 1341128008,
                'uploader_id': '327753',
                'view_count': 58939,
                'comment_count': 2656,
                'duration': 5271.0,
                'webpage_url': 'https://www.nicovideo.jp/watch/sm18238488'}
        TestCase().assertDictEqual(expected_dict, actual_dict)


if __name__ == '__main__':
    unittest.main()
