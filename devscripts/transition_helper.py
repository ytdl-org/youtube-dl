#!/usr/bin/env python

import sys, os

try:
    import urllib.request as compat_urllib_request
except ImportError: # Python 2
    import urllib2 as compat_urllib_request

sys.stderr.write(u'Hi! We changed distribution method and now youtube-dl needs to update itself one more time.\n')
sys.stderr.write(u'This will only happen once. Simply press enter to go on. Sorry for the trouble!\n')
sys.stderr.write(u'The new location of the binaries is https://github.com/rg3/youtube-dl/downloads, not the git repository.\n\n')

try:
	raw_input()
except NameError: # Python 3
	input()

filename = sys.argv[0]

API_URL = "https://api.github.com/repos/rg3/youtube-dl/downloads"
BIN_URL = "https://github.com/downloads/rg3/youtube-dl/youtube-dl"

if not os.access(filename, os.W_OK):
    sys.exit('ERROR: no write permissions on %s' % filename)

try:
    urlh = compat_urllib_request.urlopen(BIN_URL)
    newcontent = urlh.read()
    urlh.close()
except (IOError, OSError) as err:
    sys.exit('ERROR: unable to download latest version')

try:
    with open(filename, 'wb') as outf:
        outf.write(newcontent)
except (IOError, OSError) as err:
    sys.exit('ERROR: unable to overwrite current version')

sys.stderr.write(u'Done! Now you can run youtube-dl.\n')
