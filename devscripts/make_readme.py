from __future__ import unicode_literals

import os.path
import re
import sys
dirn = os.path.dirname

sys.path.insert(0, dirn(dirn(os.path.abspath(__file__))))

from utils import read_file
from youtube_dl.compat import compat_open as open

README_FILE = 'README.md'
helptext = sys.stdin.read()

if isinstance(helptext, bytes):
    helptext = helptext.decode('utf-8')

oldreadme = read_file(README_FILE)

header = oldreadme[:oldreadme.index('# OPTIONS')]
footer = oldreadme[oldreadme.index('# CONFIGURATION'):]

options = helptext[helptext.index('  General Options:') + 19:]
options = re.sub(r'(?m)^  (\w.+)$', r'## \1', options)
options = '# OPTIONS\n' + options + '\n'

with open(README_FILE, 'w', encoding='utf-8') as f:
    f.write(header)
    f.write(options)
    f.write(footer)
