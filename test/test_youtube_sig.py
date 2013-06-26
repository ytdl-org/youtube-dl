#!/usr/bin/env python

import unittest
import sys

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor.youtube import YoutubeIE
from helper import FakeYDL

sig = YoutubeIE(FakeYDL())._decrypt_signature

class TestYoutubeSig(unittest.TestCase):
    def test_43_43(self):
        wrong = '5AEEAE0EC39677BC65FD9021CCD115F1F2DBD5A59E4.C0B243A3E2DED6769199AF3461781E75122AE135135'
        right = '931EA22157E1871643FA9519676DED253A342B0C.4E95A5DBD2F1F511DCC1209DF56CB77693CE0EAE'
        self.assertEqual(sig(wrong), right)

if __name__ == '__main__':
    unittest.main()
