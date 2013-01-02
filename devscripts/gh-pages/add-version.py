#!/usr/bin/env python3

import json
import sys
import hashlib
import urllib.request

if len(sys.argv) <= 1:
	print('Specify the version number as parameter')
	sys.exit()
version = sys.argv[1]

with open('update/LATEST_VERSION', 'w') as f:
	f.write(version)

versions_info = json.load(open('update/versions.json'))
if 'signature' in versions_info:
	del versions_info['signature']

new_version = {}

filenames = {'bin': 'youtube-dl', 'exe': 'youtube-dl.exe', 'tar': 'youtube-dl-%s.tar.gz' % version}
for key, filename in filenames.items():
	print('Downloading and checksumming %s...' %filename)
	url = 'http://youtube-dl.org/downloads/%s/%s' % (version, filename)
	data = urllib.request.urlopen(url).read()
	sha256sum = hashlib.sha256(data).hexdigest()
	new_version[key] = (url, sha256sum)

versions_info['versions'][version] = new_version
versions_info['latest'] = version

json.dump(versions_info, open('update/versions.json', 'w'), indent=4, sort_keys=True)