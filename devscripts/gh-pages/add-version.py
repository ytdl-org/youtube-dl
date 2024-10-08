#!/usr/bin/env python3
from __future__ import unicode_literals

import json
import sys
import hashlib
import os.path

dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(dirn(os.path.abspath(__file__)))))

from devscripts.utils import read_file, write_file
from youtube_dl.compat import compat_open as open

if len(sys.argv) <= 1:
    print('Specify the version number as parameter')
    sys.exit()
version = sys.argv[1]

write_file('update/LATEST_VERSION', version)

versions_info = json.loads(read_file('update/versions.json'))
if 'signature' in versions_info:
    del versions_info['signature']

new_version = {}

filenames = {
    'bin': 'youtube-dl',
    'exe': 'youtube-dl.exe',
    'tar': 'youtube-dl-%s.tar.gz' % version}
build_dir = os.path.join('..', '..', 'build', version)
for key, filename in filenames.items():
    url = 'https://yt-dl.org/downloads/%s/%s' % (version, filename)
    fn = os.path.join(build_dir, filename)
    with open(fn, 'rb') as f:
        data = f.read()
    if not data:
        raise ValueError('File %s is empty!' % fn)
    sha256sum = hashlib.sha256(data).hexdigest()
    new_version[key] = (url, sha256sum)

versions_info['versions'][version] = new_version
versions_info['latest'] = version

with open('update/versions.json', 'w', encoding='utf-8') as jsonf:
    json.dumps(versions_info, jsonf, indent=4, sort_keys=True)
