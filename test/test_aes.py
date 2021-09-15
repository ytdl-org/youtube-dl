#!/usr/bin/env python

from __future__ import unicode_literals

# Allow direct execution
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.aes import _aes_decrypt, _aes_encrypt, aes_cbc_decrypt, aes_cbc_encrypt, aes_decrypt_text
from youtube_dl.utils import bytes_to_intlist, intlist_to_bytes
import base64

# the encrypted data can be generate with 'devscripts/generate_aes_testdata.py'


class TestAES(unittest.TestCase):
    def setUp(self):
        self.key = self.iv = b' \x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        self.secret_msg = b'Secret message goes here'

    def test_encrypt(self):
        msg = b'message'
        key = list(range(16))  # this considered already expanded
        encrypted = _aes_encrypt(bytes_to_intlist(msg), key)
        decrypted = intlist_to_bytes(_aes_decrypt(encrypted, key))
        self.assertEqual(decrypted, msg)

    def test_cbc_decrypt(self):
        data = b"\x97\x92+\xe5\x0b\xc3\x18\x91ky9m&\xb3\xb5@\xe6'\xc2\x96.\xc8u\x88\xab9-[\x9e|\xf1\xcd"
        decrypted = aes_cbc_decrypt(data, self.key, self.iv)
        self.assertEqual(decrypted.rstrip(b'\x08'), self.secret_msg)

    def test_cbc_encrypt(self):
        encrypted = aes_cbc_encrypt(self.secret_msg, self.key, self.iv)
        self.assertEqual(
            encrypted,
            b"\x97\x92+\xe5\x0b\xc3\x18\x91ky9m&\xb3\xb5@\xe6'\xc2\x96.\xc8u\x88\xab9-[\x9e|\xf1\xcd")

    def test_decrypt_text(self):
        password = self.key.decode('utf-8')
        encrypted = base64.b64encode(
            self.iv[:8] + b'\x17\x15\x93\xab\x8d\x80V\xcdV\xe0\t\xcdo\xc2\xa5\xd8ksM\r\xe27N\xae'
        ).decode('utf-8')
        decrypted = aes_decrypt_text(encrypted, password, 16)
        self.assertEqual(decrypted, self.secret_msg)

        password = self.key.decode('utf-8')
        encrypted = base64.b64encode(
            self.iv[:8] + b'\x0b\xe6\xa4\xd9z\x0e\xb8\xb9\xd0\xd4i_\x85\x1d\x99\x98_\xe5\x80\xe7.\xbf\xa5\x83'
        ).decode('utf-8')
        decrypted = aes_decrypt_text(encrypted, password, 32)
        self.assertEqual(decrypted, self.secret_msg)


if __name__ == '__main__':
    unittest.main()
