from __future__ import unicode_literals

import codecs
import subprocess

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_dl.aes import aes_encrypt

secret_msg = b'Secret message goes here'


def hex_str(int_list):
    return codecs.encode(int_list, 'hex')


def openssl_encode(algo, key, iv):
    cmd = ['openssl', 'enc', '-e', '-' + algo, '-K', hex_str(key), '-iv', hex_str(iv)]
    prog = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = prog.communicate(secret_msg)
    return out


iv = key = b' \x15' + b'\x00' * 14

r = openssl_encode('aes-128-cbc', key, iv)
print('aes_cbc_decrypt')
print(repr(r))

password = key
new_key = aes_encrypt(password, password)
r = openssl_encode('aes-128-ctr', new_key, iv)
print('aes_decrypt_text 16')
print(repr(r))

password = key + b'\x00' * 16
new_key = aes_encrypt(password, password) * (32 // 16)
r = openssl_encode('aes-256-ctr', new_key, iv)
print('aes_decrypt_text 32')
print(repr(r))
