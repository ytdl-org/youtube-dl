#!/usr/bin/env python3
from __future__ import unicode_literals

import json
import os.path
import sys

dirn = os.path.dirname

sys.path.insert(0, dirn(dirn((os.path.abspath(__file__)))))

from utils import read_file, write_file

versions_info = json.loads(read_file('update/versions.json'))
version = versions_info['latest']
version_dict = versions_info['versions'][version]

# Read template page
template = read_file('download.html.in')

template = template.replace('@PROGRAM_VERSION@', version)
template = template.replace('@PROGRAM_URL@', version_dict['bin'][0])
template = template.replace('@PROGRAM_SHA256SUM@', version_dict['bin'][1])
template = template.replace('@EXE_URL@', version_dict['exe'][0])
template = template.replace('@EXE_SHA256SUM@', version_dict['exe'][1])
template = template.replace('@TAR_URL@', version_dict['tar'][0])
template = template.replace('@TAR_SHA256SUM@', version_dict['tar'][1])

write_file('download.html', template)
