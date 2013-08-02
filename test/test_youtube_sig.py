#!/usr/bin/env python

import unittest
import sys

# Allow direct execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.extractor.youtube import YoutubeIE
from helper import FakeYDL

ie = YoutubeIE(FakeYDL())
sig = ie._decrypt_signature
sig_age_gate = ie._decrypt_signature_age_gate

class TestYoutubeSig(unittest.TestCase):
    def test_92(self):
        wrong = "F9F9B6E6FD47029957AB911A964CC20D95A181A5D37A2DBEFD67D403DB0E8BE4F4910053E4E8A79.0B70B.0B80B8"
        right = "69B6E6FD47029957AB911A9F4CC20D95A181A5D3.A2DBEFD67D403DB0E8BE4F4910053E4E8A7980B7"
        self.assertEqual(sig(wrong), right)

    def test_90(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<'`"
        right = "mrtyuioplkjhgfdsazxcvbne1234567890QWER[YUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={`]}|"
        self.assertEqual(sig(wrong), right)

    def test_88(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[]}|:;?/>.<"
        right = "J:|}][{=+-_)(*&;%$#@>MNBVCXZASDFGH^KLPOIUYTREWQ0987654321mnbvcxzasdfghrklpoiuytej"
        self.assertEqual(sig(wrong), right)

    def test_87(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>.<"
        right = "tyuioplkjhgfdsazxcv<nm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$^&*()_-+={[]}|:;?/>"
        self.assertEqual(sig(wrong), right)

    def test_86(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<"
        right = ">.1}|[{=+-_)(*&^%$#@!MNBVCXZASDFGHJK<POIUYTREW509876L432/mnbvcxzasdfghjklpoiuytre"
        self.assertEqual(sig(wrong), right)

    def test_85(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?/>.<"
        right = "ertyuiqplkjhgfdsazx$vbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#<%^&*()_-+={[};?/c"
        self.assertEqual(sig(wrong), right)

    def test_84(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[};?>.<"
        right = "<.>?;}[{=+-_)(*&^%$#@!MNBVCXZASDFGHJKLPOIUYTREWe098765432rmnbvcxzasdfghjklpoiuyt1"
        self.assertEqual(sig(wrong), right)

    def test_83(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/>.<"
        right = "qwertyuioplkjhg>dsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!#$%^&*()_+={[};?/f"
        self.assertEqual(sig(wrong), right)

    def test_82(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>.<"
        right = "Q>/?;}[{=+-(*<^%$#@!MNBVCXZASDFGHKLPOIUY8REWT0q&7654321mnbvcxzasdfghjklpoiuytrew9"
        self.assertEqual(sig(wrong), right)

    def test_81(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/>."
        right = "C>/?;}[{=+-(*&^%$#@!MNBVYXZASDFGHKLPOIU.TREWQ0q87659321mnbvcxzasdfghjkl4oiuytrewp"
        self.assertEqual(sig(wrong), right)

    def test_79(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKHGFDSAZXCVBNM!@#$%^&*(-+={[};?/"
        right = "Z?;}[{=+-(*&^%$#@!MNBVCXRASDFGHKLPOIUYT/EWQ0q87659321mnbvcxzasdfghjkl4oiuytrewp"
        self.assertEqual(sig(wrong), right)
    
    def test_86_age_gate(self):
        wrong = "qwertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!@#$%^&*()_-+={[|};?/>.<"
        right = "ertyuioplkjhgfdsazxcvbnm1234567890QWERTYUIOPLKJHGFDSAZXCVBNM!/#$%^&*()_-+={[|};?@"
        self.assertEqual(sig_age_gate(wrong), right)

if __name__ == '__main__':
    unittest.main()
