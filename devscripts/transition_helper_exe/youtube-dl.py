#!/usr/bin/env python

import sys, os
import urllib2

sys.stderr.write(u'Hi! We changed distribution method and now youtube-dl needs to update itself one more time.\n')
sys.stderr.write(u'This will only happen once. Simply press enter to go on. Sorry for the trouble!\n')
sys.stderr.write(u'The new location of the binaries is https://github.com/rg3/youtube-dl/downloads, not the git repository.\n\n')

raw_input()

filename = sys.argv[0]

API_URL = "https://api.github.com/repos/rg3/youtube-dl/downloads"
EXE_URL = "https://github.com/downloads/rg3/youtube-dl/youtube-dl.exe"

if not os.access(filename, os.W_OK):
    sys.exit('ERROR: no write permissions on %s' % filename)

exe = os.path.abspath(filename)
directory = os.path.dirname(exe)
if not os.access(directory, os.W_OK):
    sys.exit('ERROR: no write permissions on %s' % directory)

try:
    urlh = urllib2.urlopen(EXE_URL)
    newcontent = urlh.read()
    urlh.close()
    with open(exe + '.new', 'wb') as outf:
        outf.write(newcontent)
except (IOError, OSError) as err:
    sys.exit('ERROR: unable to download latest version')

try:
    bat = os.path.join(directory, 'youtube-dl-updater.bat')
    b = open(bat, 'w')
    b.write("""
echo Updating youtube-dl...
ping 127.0.0.1 -n 5 -w 1000 > NUL
move /Y "%s.new" "%s"
del "%s"
    \n""" %(exe, exe, bat))
    b.close()

    os.startfile(bat)
except (IOError, OSError) as err:
    sys.exit('ERROR: unable to overwrite current version')

sys.stderr.write(u'Done! Now you can run youtube-dl.\n')
