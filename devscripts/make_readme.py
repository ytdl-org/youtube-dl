import sys
import re

README_FILE = 'README.md'
helptext = sys.stdin.read()

with open(README_FILE) as f:
    oldreadme = f.read()

header = oldreadme[:oldreadme.index('# OPTIONS')]
footer = oldreadme[oldreadme.index('# CONFIGURATION'):]

options = helptext[helptext.index('  General Options:')+19:]
options = re.sub(r'^  (\w.+)$', r'## \1', options, flags=re.M)
options = '# OPTIONS\n' + options + '\n'

with open(README_FILE, 'w') as f:
    f.write(header)
    f.write(options)
    f.write(footer)
