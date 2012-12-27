#! /usr/bin/env python3

import rsa
import json
from binascii import hexlify

# TODO path discovery
versions_info = json.load(open('versions.json'))
if 'signature' in versions_info:
	del versions_info['signature']


print('Enter the PKCS1 private key, followed by a blank line:')
privkey = ''
while True:
	try:
		line = input()
	except EOFError:
		break
	if line == '':
		break
	privkey += line + '\n'
privkey = bytes(privkey, 'ascii')
privkey = rsa.PrivateKey.load_pkcs1(privkey)

signature = hexlify(rsa.pkcs1.sign(json.dumps(versions_info, sort_keys=True).encode('utf-8'), privkey, 'SHA-256'))
print('signature: ' + signature.decode())