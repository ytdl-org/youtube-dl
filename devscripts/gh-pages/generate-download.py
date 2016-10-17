#!/usr/bin/env python3
from __future__ import unicode_literals

import hashlib
import urllib.request
import json

versions_info = json.load(open('update/versions.json'))
version = versions_info['latest']
URL = versions_info['versions'][version]['bin'][0]

data = urllib.request.urlopen(URL).read()

# Read template page
with open('download.html.in', 'r', encoding='utf-8') as tmplf:
    template = tmplf.read()

sha256sum = hashlib.sha256(data).hexdigest()
template = template.replace('@PROGRAM_VERSION@', version)
template = template.replace('@PROGRAM_URL@', URL)
template = template.replace('@PROGRAM_SHA256SUM@', sha256sum)
template = template.replace('@EXE_URL@', versions_info['versions'][version]['exe'][0])
template = template.replace('@EXE_SHA256SUM@', versions_info['versions'][version]['exe'][1])
template = template.replace('@TAR_URL@', versions_info['versions'][version]['tar'][0])
template = template.replace('@TAR_SHA256SUM@', versions_info['versions'][version]['tar'][1])
with open('download.html', 'w', encoding='utf-8') as dlf:
    dlf.write(template)
