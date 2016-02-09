import os.path
import youtube_dl
import sys

#sys.argv.append('http://trailers.apple.com/trailers/fox/kungfupanda3/')
#sys.argv.append('--verbose')

scriptArgs = "--verbose http://trailers.apple.com/trailers/fox/kungfupanda3/"

sys.argv.extend(scriptArgs.split(' '))

youtube_dl.main()