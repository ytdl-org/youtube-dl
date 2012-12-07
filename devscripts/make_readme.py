import sys
import re

helptext = sys.stdin.read()

f = open('README.md')
oldreadme = f.read()
f.close()

header = oldreadme[:oldreadme.index('# OPTIONS')]
footer = oldreadme[oldreadme.index('# CONFIGURATION'):]

options = helptext[helptext.index('  General Options:')+19:]
options = re.sub(r'^  (\w.+)$', r'## \1', options, flags=re.M)
options = '# OPTIONS\n' + options + '\n'

f = open('README.md', 'w')
f.write(header)
f.write(options)
f.write(footer)
f.close()