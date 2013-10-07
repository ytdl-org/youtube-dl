#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
  youtube-dl (--help | --version)
  youtube-dl URL ... [options]

Options:
  General Options:
    -h --help                  print this help text and exit
    --version                  print program version and exit
    -U --update                update this program to latest version. Make sure
                               that you have sufficient permissions (run with
                               sudo if needed)
    -i --ignore-errors         continue on download errors, for example to to
                               skip unavailable videos in a playlist
    --dump-user-agent          display the current browser identification
    --user-agent=UA            specify a custom user agent
    --referer=REF              specify a custom referer, use if the video access
                               is restricted to one domain
    --list-extractors          List all supported extractors and the URLs they
                               would handle
    --extractor-descriptions   Output descriptions of all supported extractors
    --proxy=URL                Use the specified HTTP/HTTPS proxy
    --no-check-certificate     Suppress HTTPS certificate validation.
    --cache-dir                Location in the filesystem where youtube-dl can
                               store downloaded information permanently. By
                               default $XDG_CACHE_HOME/youtube-dl or ~/.cache
                               /youtube-dl .
    --no-cache-dir             Disable filesystem caching

  Video Selection Options:
    --playlist-start=NUMBER    playlist video to start at [default: 1]
    --playlist-end=NUMBER      playlist video to end at (defaults to last)
                               [default: -1]
    --match-title=REGEX        download only matching titles (regex or caseless
                               sub-string)
    --reject-title=REGEX       skip download for matching titles (regex or
                               caseless sub-string)
    --max-downloads=NUMBER     Abort after downloading NUMBER files
    --min-filesize=SIZE        Do not download any videos smaller than SIZE
                               (e.g. 50k or 44.6m)
    --max-filesize=SIZE        Do not download any videos larger than SIZE (e.g.
                               50k or 44.6m)
    --date=DATE                download only videos uploaded in this date
    --datebefore=DATE          download only videos uploaded before this date
    --dateafter=DATE           download only videos uploaded after this date
    --no-playlist              download only the currently playing video

  Download Options:
    -r --rate-limit=LIMIT      maximum download rate (e.g. 50k or 44.6m)
    -R --retries=RETRIES       number of retries [default: 10]
    --buffer-size=SIZE         size of download buffer (e.g. 1024 or 16k)
                               [default: 1024]
    --no-resize-buffer         do not automatically adjust the buffer size. By
                               default, the buffer size is automatically resized
                               from an initial value of SIZE.

  Filesystem Options:
    -t --title                 use title in file name (default action)
    --id                       use only video ID in file name
    -A --auto-number           number downloaded files starting from 00000
    -o --output=TEMPLATE       output filename template. Use %(title)s to get
                               the title, %(uploader)s for the uploader name,
                               %(uploader_id)s for the uploader nickname if
                               different, %(autonumber)s to get an automatically
                               incremented number, %(ext)s for the filename
                               extension, %(upload_date)s for the upload date
                               (YYYYMMDD), %(extractor)s for the provider
                               (youtube, metacafe, etc), %(id)s for the video id
                               , %(playlist)s for the playlist the video is in,
                               %(playlist_index)s for the position in the
                               playlist and %% for a literal percent. Use - to
                               output to stdout. Can also be used to download to
                               a different directory, for example with -o '/my/d
                               ownloads/%(uploader)s/%(title)s-%(id)s.%(ext)s' .
    --autonumber-size=NUMBER   Specifies the number of digits in %(autonumber)s
                               when it is present in output filename template or
                               --autonumber option is given
    --restrict-filenames       Restrict filenames to only ASCII characters, and
                               avoid "&" and spaces in filenames
    -a --batch-file=FILE       file containing URLs to download ('-' for stdin)
    -w --no-overwrites         do not overwrite files
    -c --continue              resume partially downloaded files
    --no-continue              do not resume partially downloaded files (restart
                               from beginning)
    --cookies=FILE             file to read cookies from and dump cookie jar in
    --no-part                  do not use .part files
    --no-mtime                 do not use the Last-modified header to set the
                               file modification time
    --write-description        write video description to a .description file
    --write-info-json          write video metadata to a .info.json file
    --write-thumbnail          write thumbnail image to disk

  Verbosity / Simulation Options:
    -q --quiet                 activates quiet mode
    -s --simulate              do not download the video and do not write
                               anything to disk
    --skip-download            do not download the video
    -g --get-url               simulate, quiet but print URL
    -e --get-title             simulate, quiet but print title
    --get-id                   simulate, quiet but print id
    --get-thumbnail            simulate, quiet but print thumbnail URL
    --get-description          simulate, quiet but print video description
    --get-filename             simulate, quiet but print output filename
    --get-format               simulate, quiet but print output format
    --newline                  output progress bar as new lines
    --no-progress              do not print progress bar
    --console-title            display progress in console titlebar
    -v --verbose               print various debugging information
    --dump-intermediate-pages  print downloaded pages to debug problems(very
                               verbose)
    --test                     Download only first bytes to test the downloader

  Video Format Options:
    -f --format=FORMAT         video format code, specifiy the order of
                               preference using slashes: "-f 22/17/18". "-f mp4"
                               and "-f flv" are also supported
    --all-formats              download all available video formats
    --prefer-free-formats      prefer free video formats unless a specific one
                               is requested
    --max-quality=FORMAT       highest quality format to download
    -F --list-formats          list all available formats (currently youtube
                               only)

  Subtitle Options:
    --write-sub                write subtitle file
    --write-auto-sub           write automatic subtitle file (youtube only)
    --all-subs                 downloads all the available subtitles of the
                               video
    --list-subs                lists all available subtitles for the video
    --sub-format=FORMAT        subtitle format ([sbv/vtt] youtube only)
                               [default: srt]
    --sub-langs=LANGS ...      languages of the subtitles to download (optional,
                               multiple arguments) use IETF language tags like
                               'en,pt'

  Authentication Options:
    -u --username=USERNAME     account username
    -p --password=PASSWORD     account password
    -n --netrc                 use .netrc authentication data
    --video-password=PASSWORD  video password (vimeo only)

  Post-processing Options:
    -x --extract-audio         convert video files to audio-only files (requires
                               ffmpeg or avconv and ffprobe or avprobe)
    --audio-format=FORMAT      "best", "aac", "vorbis", "mp3", "m4a", "opus", or
                               "wav"; [default: best]
    --audio-quality=QUALITY    ffmpeg/avconv audio quality specification, insert
                               a value between 0 (better) and 9 (worse) for VBR
                               or a specific bitrate like 128K [default: 5]
    --recode-video=FORMAT      Encode the video to another format if necessary
                               (currently supported: mp4|flv|ogg|webm)
    -k --keep-video            keeps the video file on disk after the post-
                               processing; the video is erased by default
    --no-post-overwrites       do not overwrite post-processed files; the post-
                               processed files are overwritten by default
    --embed-subs               embed subtitles in the video (only for mp4
                               videos)
"""

__authors__ = (
    'Ricardo Garcia Gonzalez',
    'Danny Colligan',
    'Benjamin Johnson',
    'Vasyl\' Vavrychuk',
    'Witold Baryluk',
    'Paweł Paprota',
    'Gergely Imreh',
    'Rogério Brito',
    'Philipp Hagemeister',
    'Sören Schulze',
    'Kevin Ngo',
    'Ori Avtalion',
    'shizeeg',
    'Filippo Valsorda',
    'Christian Albrecht',
    'Dave Vasilevsky',
    'Jaime Marquínez Ferrándiz',
    'Jeff Crouse',
    'Osama Khalid',
    'Michael Walter',
    'M. Yasoob Ullah Khalid',
    'Julien Fraichard',
    'Johny Mo Swag',
    'Axel Noack',
    'Albert Kim',
    'Pierre Rudloff',
    'Huarong Huo',
    'Ismael Mejía',
    'Paul Barton'
)

__license__ = 'Public Domain'

import codecs
import getpass
import os
import random
import re
#import shlex
import socket
import subprocess
import sys
#import warnings
import platform

from .docopt import docopt
from .utils import *
from .update import update_self
from .version import __version__
from .FileDownloader import *
from .extractor import gen_extractors
from .YoutubeDL import YoutubeDL
from .PostProcessor import *

class OptionsError(Exception):
    pass

def _real_main():
    # Compatibility fixes for Windows
    if sys.platform == 'win32':
        # https://github.com/rg3/youtube-dl/issues/820
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    opts = docopt(__doc__, version=__version__)
    #--all-formats will supersede --format
    if opts['--all-formats']:
        opts['--format'] = 'all'
    #--continue and --no-continue are mutually exclusive and control the
    #partial downloading of files
    if opts['--no-continue']:
        opts['--continue'] = False
    else:
        opts['--continue'] = True
    #Invert boolean value of opts['--no-mtime']
    opts['--no-mtime'] = not opts['--no-mtime']

    # Open appropriate CookieJar
    if not opts['--cookies']:
        jar = compat_cookiejar.CookieJar()
    else:
        try:
            jar = compat_cookiejar.MozillaCookieJar(opts['--cookies'])
            if os.access(opts['--cookies'], os.R_OK):
                jar.load()
        except (IOError, OSError) as err:
            if opts['--verbose']:
                traceback.print_exc()
            sys.stderr.write(u'ERROR: unable to open cookie file\n')
            sys.exit(101)
    # Set user agent
    if opts['--user-agent']:
        std_headers['User-Agent'] = opts['--user-agent']

    # Set referer
    if opts['--referer']:
        std_headers['Referer'] = opts['--referer']

    # Dump user agent
    if opts['--dump-user-agent']:
        compat_print(std_headers['User-Agent'])
        sys.exit(0)

    # Batch file verification
    batchurls = []
    if opts['--batch-file']:
        try:
            if opts['--batch-file'] == '-':
                batchfd = sys.stdin
            else:
                batchfd = open(opts['--batch-file'], 'r')
            batchurls = batchfd.readlines()
            batchurls = [x.strip() for x in batchurls]
            batchurls = [x for x in batchurls if len(x) > 0 and not re.search(r'^[#/;]', x)]
            if opts['--verbose']:
                sys.stderr.write(u'[debug] Batch file urls: ' + repr(batchurls) + u'\n')
        except IOError:
            sys.exit(u'ERROR: batch file could not be read')
    all_urls = batchurls + opts['URL']
    print(all_urls)
    all_urls = [url.strip() for url in all_urls]

    # General configuration
    cookie_processor = compat_urllib_request.HTTPCookieProcessor(jar)
    if opts['--proxy']:
        if opts['--proxy'] == '':  # Will this ever happen?
            proxies = {}
        else:
            proxies = {'http': opts['--proxy'], 'https': opts['--proxy']}
    else:
        proxies = compat_urllib_request.getproxies()
        # Set HTTPS proxy to HTTP one if given (https://github.com/rg3/youtube-dl/issues/805)
        if 'http' in proxies and 'https' not in proxies:
            proxies['https'] = proxies['http']
    proxy_handler = compat_urllib_request.ProxyHandler(proxies)
    https_handler = make_HTTPS_handler(opts)
    opener = compat_urllib_request.build_opener(https_handler, proxy_handler, cookie_processor, YoutubeDLHandler())
    # Delete the default user-agent header, which would otherwise apply in
    # cases where our custom HTTP handler doesn't come into play
    # (See https://github.com/rg3/youtube-dl/issues/1309 for details)
    opener.addheaders =[]
    compat_urllib_request.install_opener(opener)
    socket.setdefaulttimeout(300) # 5 minutes should be enough (famous last words)

    extractors = gen_extractors()

    if opts['--list-extractors']:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            compat_print(ie.IE_NAME + (' (CURRENTLY BROKEN)' if not ie._WORKING else ''))
            matchedUrls = [url for url in all_urls if ie.suitable(url)]
            all_urls = [url for url in all_urls if url not in matchedUrls]
            for mu in matchedUrls:
                compat_print(u'  ' + mu)
        sys.exit(0)
    if opts['--extractor-descriptions']:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            if not ie._WORKING:
                continue
            desc = getattr(ie, 'IE_DESC', ie.IE_NAME)
            if hasattr(ie, 'SEARCH_KEY'):
                _SEARCHES = (u'cute kittens', u'slithering pythons', u'falling cat', u'angry poodle', u'purple fish', u'running tortoise')
                _COUNTS = (u'', u'5', u'10', u'all')
                desc += u' (Example: "%s%s:%s" )' % (ie.SEARCH_KEY, random.choice(_COUNTS), random.choice(_SEARCHES))
            compat_print(desc)
        sys.exit(0)


    # Conflicting, missing and erroneous options
    if opts['--netrc'] and (opts['--username'] or opts['--password']):
        raise OptionsError(u'using .netrc conflicts with giving username/password')
    if opts['--password'] and not opts['--username']:
        raise OptionsError(u' account username missing\n')
    if opts['--username'] and not opts['--password']:
        opts['--password'] = getpass.getpass(u'Type account password and press return:')
    if opts['--output'] and (opts['--title'] or opts['--auto-number'] or opts['--id']):
        raise OptionsError(u'using output template conflicts with using title, video ID or auto number')
    if opts['--title'] and opts['--id']:
        raise OptionsError(u'using title conflicts with using video ID')
    if opts['--rate-limit']:
        numeric_limit = FileDownloader.parse_bytes(opts['--rate-limit'])
        if numeric_limit is None:
            raise OptionsError(u'invalid rate limit specified')
        opts['--rate-limit'] = numeric_limit
    if opts['--min-filesize']:
        numeric_limit = FileDownloader.parse_bytes(opts['--min-filesize'])
        if numeric_limit is None:
            raise OptionsError(u'invalid min_filesize specified')
        opts['--min-filesize'] = numeric_limit
    if opts['--max-filesize']:
        numeric_limit = FileDownloader.parse_bytes(opts['--max-filesize'])
        if numeric_limit is None:
            raise OptionsError(u'invalid max_filesize specified')
        opts['--max-filesize'] = numeric_limit
    if opts['--retries'] is not None:  # This should always be true, it has a default
        try:
            opts['--retries'] = int(opts['--retries'])
        except (TypeError, ValueError) as err:
            raise OptionsError(u'invalid retry count specified')
    if opts['--buffer-size'] is not None:  # This should always be true, it has a default
        numeric_buffersize = FileDownloader.parse_bytes(opts['--buffer-size'])
        if numeric_buffersize is None:
            raise OptionsError(u'invalid buffer size specified')
        opts['--buffer-size'] = numeric_buffersize
    try:
        opts['--playlist-start'] = int(opts['--playlist-start'])
        if opts['--playlist-start'] <= 0:
            raise ValueError(u'Playlist start must be positive')
    except (TypeError, ValueError) as err:
        raise OptionsError(u'invalid playlist start number specified')
    try:
        opts['--playlist-end'] = int(opts['--playlist-end'])
        if opts['--playlist-end'] != -1 and (opts['--playlist-end'] <= 0 or opts['--playlist-end'] < opts['--playlist-start']):
            raise ValueError(u'Playlist end must be greater than playlist start')
    except (TypeError, ValueError) as err:
        raise OptionsError(u'invalid playlist end number specified')
    if opts['--extract-audio']:
        if opts['--audio-format'] not in ['best', 'aac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
            raise OptionsError(u'invalid audio format specified')
    if opts['--audio-quality']:
        opts['--audio-quality'] = opts['--audio-quality'].strip('k').strip('K')
        if not opts['--audio-quality'].isdigit():
            raise OptionsError(u'invalid audio quality specified')
    if opts['--recode-video']:
        if opts['--recode-video'] not in ['mp4', 'flv', 'webm', 'ogg']:
            raise OptionsError(u'invalid video recode format specified')
    if opts['--date']:
        date = DateRange.day(opts['--date'])
    else:
        date = DateRange(opts['--dateafter'], opts['--datebefore'])

    if sys.version_info < (3,):
        # In Python 2, sys.argv is a bytestring (also note http://bugs.python.org/issue2128 for Windows systems)
        if opts['--output']:
            opts['--output'] = opts['--output'].decode(preferredencoding())
    outtmpl =((opts['--output'] is not None and opts['--output'])
            or (opts['--format'] == '-1' and opts['--title'] and u'%(title)s-%(id)s-%(format)s.%(ext)s')  # Why would --format ever be -1 ?
            or (opts['--format'] == '-1' and u'%(id)s-%(format)s.%(ext)s')  # Why would --format ever be -1 ?
            or (opts['--title'] and opts['--auto-number'] and u'%(autonumber)s-%(title)s-%(id)s.%(ext)s')
            or (opts['--title'] and u'%(title)s-%(id)s.%(ext)s')
            or (opts['--id'] and u'%(id)s.%(ext)s')
            or (opts['--auto-number'] and u'%(autonumber)s-%(id)s.%(ext)s')
            or u'%(title)s-%(id)s.%(ext)s')

    # YoutubeDL
    ydl = YoutubeDL({
        'usenetrc': opts['--netrc'],
        'username': opts['--username'],
        'password': opts['--password'],
        'videopassword': opts['--video-password'],
        'quiet': (opts['--quiet'] or opts['--get-url'] or opts['--get-title'] or opts['--get-id'] or opts['--get-thumbnail'] or opts['--get-description'] or opts['--get-filename'] or opts['--get-format']),
        'forceurl': opts['--get-url'],
        'forcetitle': opts['--get-title'],
        'forceid': opts['--get-id'],
        'forcethumbnail': opts['--get-thumbnail'],
        'forcedescription': opts['--get-description'],
        'forcefilename': opts['--get-filename'],
        'forceformat': opts['--get-format'],
        'simulate': opts['--simulate'],
        'skip_download': (opts['--skip-download'] or opts['--simulate'] or opts['--get-url'] or opts['--get-title'] or opts['--get-id'] or opts['--get-thumbnail'] or opts['--get-description'] or opts['--get-filename'] or opts['--get-format']),
        'format': opts['--format'],
        'format_limit': opts['--max-quality'],
        'listformats': opts['--list-formats'],
        'outtmpl': outtmpl,
        'autonumber_size': opts['--autonumber-size'],
        'restrictfilenames': opts['--restrict-filenames'],
        'ignoreerrors': opts['--ignore-errors'],
        'ratelimit': opts['--rate-limit'],
        'nooverwrites': opts['--no-overwrites'],
        'retries': opts['--retries'],
        'buffersize': opts['--buffer-size'],
        'noresizebuffer': opts['--no-resize-buffer'],
        'continuedl': opts['--continue'],
        'noprogress': opts['--no-progress'],
        'progress_with_newline': opts['--newline'],
        'playliststart': opts['--playlist-start'],
        'playlistend': opts['--playlist-end'],
        'logtostderr': opts['--output'] == '-',
        'consoletitle': opts['--console-title'],
        'nopart': opts['--no-part'],
        'updatetime': opts['--no-mtime'],
        'writedescription': opts['--write-description'],
        'writeinfojson': opts['--write-info-json'],
        'writethumbnail': opts['--write-thumbnail'],
        'writesubtitles': opts['--write-sub'],
        'writeautomaticsub': opts['--write-auto-sub'],
        'allsubtitles': opts['--all-subs'],
        'listsubtitles': opts['--list-subs'],
        'subtitlesformat': opts['--sub-format'],
        'subtitleslangs': opts['--sub-langs'],
        'matchtitle': decodeOption(opts['--match-title']),
        'rejecttitle': decodeOption(opts['--reject-title']),
        'max_downloads': opts['--max-downloads'],
        'prefer_free_formats': opts['--prefer-free-formats'],
        'verbose': opts['--verbose'],
        'dump_intermediate_pages': opts['--dump-intermediate-pages'],
        'test': opts['--test'],
        'keepvideo': opts['--keep-video'],
        'min_filesize': opts['--min-filesize'],
        'max_filesize': opts['--max-filesize'],
        'daterange': date,
        })

    if opts['--verbose']:
        sys.stderr.write(u'[debug] youtube-dl version ' + __version__ + u'\n')
        try:
            sp = subprocess.Popen(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            out, err = sp.communicate()
            out = out.decode().strip()
            if re.match('[0-9a-f]+', out):
                sys.stderr.write(u'[debug] Git HEAD: ' + out + u'\n')
        except:
            try:
                sys.exc_clear()
            except:
                pass
        sys.stderr.write(u'[debug] Python version %s - %s' %(platform.python_version(), platform_name()) + u'\n')
        sys.stderr.write(u'[debug] Proxy map: ' + str(proxy_handler.proxies) + u'\n')

    ydl.add_default_info_extractors()

    # PostProcessors
    if opts['--extract-audio']:
        ydl.add_post_processor(FFmpegExtractAudioPP(preferredcodec=opts['--audio-format'], preferredquality=opts['--audio-quality'], nopostoverwrites=opts['--no-post-overwrites']))
    if opts['--recode-video']:
        ydl.add_post_processor(FFmpegVideoConvertor(preferedformat=opts['--recode-video']))
    if opts['--embed-subs']:
        ydl.add_post_processor(FFmpegEmbedSubtitlePP(subtitlesformat=opts['--sub-format']))

    # Update version
    if opts['--update']:
        update_self(ydl.to_screen, opts['--verbose'], sys.argv[0])

    # Maybe do nothing
    if len(all_urls) < 1:
        if not opts['--update']:
            raise OptionsError(u'you must provide at least one URL')
        else:
            sys.exit()

    try:
        retcode = ydl.download(all_urls)
    except MaxDownloadsReached:
        ydl.to_screen(u'--max-download limit reached, aborting.')
        retcode = 101

    # Dump cookie jar if requested
    if opts['--cookies']:
        try:
            jar.save()
        except (IOError, OSError) as err:
            sys.exit(u'ERROR: unable to save cookie jar')

    sys.exit(retcode)

def main(argv=None):
    try:
        _real_main()
    except DownloadError:
        sys.exit(1)
    except SameFileError:
        sys.exit(u'ERROR: fixed output name but more than one file to download')
    except KeyboardInterrupt:
        sys.exit(u'\nERROR: Interrupted by user')
