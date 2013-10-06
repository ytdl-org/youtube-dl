#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
  youtube-dl [--help] [--version] [--update] [--ignore-errors]
             [--dump-user-agent] [--user-agent UA] [--referer REF]
             [--list-extractors] [--extractor-descriptions] [--proxy URL]
             [--no-check-certificate] [--cache-dir] [--no-cache-dir]
             [--playlist-start NUMBER] [--playlist-end NUMBER]
             [--match-title REGEX] [--reject-title REGEX]
             [--max-downloads NUMBER] [--min-filesize SIZE]
             [--max-filesize SIZE] [--date DATE] [--datebefore DATE]
             [--dateafter DATE] [--no-playlist] [--rate-limit LIMIT]
             [--retries RETRIES] [--buffer-size SIZE] [--no-resize-buffer]
             [[--title --literal | --id] --auto-number | --output TEMPLATE]
             [--autonumber-size NUMBER] [--restrict-filenames]
             [--batch-file FILE] [--no-overwrites] [--continue | --no-continue]
             [--cookies FILE] [--no-part] [--no-mtime] [--write-description]
             [--write-info-json] [--write-thumbnail] [--quiet] [--simulate]
             [--skip-download] [--get-url] [--get-title] [--get-id]
             [--get-thumbnail] [--get-description] [--get-filename]
             [--get-format] [--newline] [--no-progress] [--console-title]
             [--verbose] [--dump-intermediate-pages] [--format FORMAT]
             [--all-formats] [--prefer-free-formats] [--max-quality FORMAT]
             [--list-formats] [--write-sub] [--write-auto-sub] [--all-subs]
             [--list-subs] [--sub-format FORMAT] [--sub-langs LANGS ...]
             [--username USERNAME --password PASSWORD | --netrc]
             [--video-password PASSWORD] [--extract-audio]
             [--audio-format FORMAT] [--audio-quality QUALITY]
             [--recode-video FORMAT] [--keep-video] [--no-post-overwrites]
             [--embed-subs]
             URL [url ...]

Options:
  General Options:
    -h, --help                 print this help text and exit
    --version                  print program version and exit
    -U, --update               update this program to latest version. Make sure
                               that you have sufficient permissions (run with
                               sudo if needed)
    -i, --ignore-errors        continue on download errors, for example to to
                               skip unavailable videos in a playlist
    --dump-user-agent          display the current browser identification
    --user-agent UA            specify a custom user agent
    --referer REF              specify a custom referer, use if the video access
                               is restricted to one domain
    --list-extractors          List all supported extractors and the URLs they
                               would handle
    --extractor-descriptions   Output descriptions of all supported extractors
    --proxy URL                Use the specified HTTP/HTTPS proxy
    --no-check-certificate     Suppress HTTPS certificate validation.
    --cache-dir None           Location in the filesystem where youtube-dl can
                               store downloaded information permanently. By
                               default $XDG_CACHE_HOME/youtube-dl or ~/.cache
                               /youtube-dl .
    --no-cache-dir             Disable filesystem caching

  Video Selection:
    --playlist-start NUMBER    playlist video to start at [default: 1]
    --playlist-end NUMBER      playlist video to end at (defaults to last)
                               [default: -1]
    --match-title REGEX        download only matching titles (regex or caseless
                               sub-string)
    --reject-title REGEX       skip download for matching titles (regex or
                               caseless sub-string)
    --max-downloads NUMBER     Abort after downloading NUMBER files
    --min-filesize SIZE        Do not download any videos smaller than SIZE
                               (e.g. 50k or 44.6m)
    --max-filesize SIZE        Do not download any videos larger than SIZE (e.g.
                               50k or 44.6m)
    --date DATE                download only videos uploaded in this date
    --datebefore DATE          download only videos uploaded before this date
    --dateafter DATE           download only videos uploaded after this date
    --no-playlist              download only the currently playing video

  Download Options:
    -r, --rate-limit LIMIT     maximum download rate (e.g. 50k or 44.6m)
    -R, --retries RETRIES      number of retries [default: 10]
    --buffer-size SIZE         size of download buffer (e.g. 1024 or 16k)
                               [default: 1024]
    --no-resize-buffer         do not automatically adjust the buffer size. By
                               default, the buffer size is automatically resized
                               from an initial value of SIZE.

  Filesystem Options:
    -t, --title                use title in file name (default)
    --id                       use only video ID in file name
    -l, --literal              [deprecated] alias of --title
    -A, --auto-number          number downloaded files starting from 00000
    -o, --output TEMPLATE      output filename template. Use %(title)s to get
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
    --autonumber-size NUMBER   Specifies the number of digits in %(autonumber)s
                               when it is present in output filename template or
                               --autonumber option is given
    --restrict-filenames       Restrict filenames to only ASCII characters, and
                               avoid "&" and spaces in filenames
    -a, --batch-file FILE      file containing URLs to download ('-' for stdin)
    -w, --no-overwrites        do not overwrite files
    -c, --continue             resume partially downloaded files
    --no-continue              do not resume partially downloaded files (restart
                               from beginning)
    --cookies FILE             file to read cookies from and dump cookie jar in
    --no-part                  do not use .part files
    --no-mtime                 do not use the Last-modified header to set the
                               file modification time
    --write-description        write video description to a .description file
    --write-info-json          write video metadata to a .info.json file
    --write-thumbnail          write thumbnail image to disk

  Verbosity / Simulation Options:
    -q, --quiet                activates quiet mode
    -s, --simulate             do not download the video and do not write
                               anything to disk
    --skip-download            do not download the video
    -g, --get-url              simulate, quiet but print URL
    -e, --get-title            simulate, quiet but print title
    --get-id                   simulate, quiet but print id
    --get-thumbnail            simulate, quiet but print thumbnail URL
    --get-description          simulate, quiet but print video description
    --get-filename             simulate, quiet but print output filename
    --get-format               simulate, quiet but print output format
    --newline                  output progress bar as new lines
    --no-progress              do not print progress bar
    --console-title            display progress in console titlebar
    -v, --verbose              print various debugging information
    --dump-intermediate-pages  print downloaded pages to debug problems(very
                               verbose)

  Video Format Options:
    -f, --format FORMAT        video format code, specifiy the order of
                               preference using slashes: "-f 22/17/18". "-f mp4"
                               and "-f flv" are also supported
    --all-formats              download all available video formats
    --prefer-free-formats      prefer free video formats unless a specific one
                               is requested
    --max-quality FORMAT       highest quality format to download
    -F, --list-formats         list all available formats (currently youtube
                               only)

  Subtitle Options:
    --write-sub                write subtitle file
    --write-auto-sub           write automatic subtitle file (youtube only)
    --all-subs                 downloads all the available subtitles of the
                               video
    --list-subs                lists all available subtitles for the video
    --sub-format FORMAT        subtitle format ([sbv/vtt] youtube only)
                               [default: srt]
    --sub-langs LANGS ...      languages of the subtitles to download (optional,
                               multiple arguments) use IETF language tags like
                               'en,pt'

  Authentication Options:
    -u, --username USERNAME    account username
    -p, --password PASSWORD    account password
    -n, --netrc                use .netrc authentication data
    --video-password PASSWORD  video password (vimeo only)

  Post-processing Options:
    -x, --extract-audio        convert video files to audio-only files (requires
                               ffmpeg or avconv and ffprobe or avprobe)
    --audio-format FORMAT      "best", "aac", "vorbis", "mp3", "m4a", "opus", or
                               "wav"; [default: best]
    --audio-quality QUALITY    ffmpeg/avconv audio quality specification, insert
                               a value between 0 (better) and 9 (worse) for VBR
                               or a specific bitrate like 128K [default: 5]
    --recode-video FORMAT      Encode the video to another format if necessary
                               (currently supported: mp4|flv|ogg|webm)
    -k, --keep-video           keeps the video file on disk after the post-
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
#import optparse
import os
import random
import re
import shlex
import socket
import subprocess
import sys
import warnings
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

def parseOpts(overrideArguments=None):
    def _readOptions(filename_bytes):
        try:
            optionf = open(filename_bytes)
        except IOError:
            return [] # silently skip if file is not present
        try:
            res = []
            for l in optionf:
                res += shlex.split(l, comments=True)
        finally:
            optionf.close()
        return res

    def _format_option_string(option):
        ''' ('-o', '--option') -> -o, --format METAVAR'''

        opts = []

        if option._short_opts:
            opts.append(option._short_opts[0])
        if option._long_opts:
            opts.append(option._long_opts[0])
        if len(opts) > 1:
            opts.insert(1, ', ')

        if option.takes_value(): opts.append(' %s' % option.metavar)

        return "".join(opts)

    def _comma_separated_values_options_callback(option, opt_str, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    def _find_term_columns():
        columns = os.environ.get('COLUMNS', None)
        if columns:
            return int(columns)

        try:
            sp = subprocess.Popen(['stty', 'size'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out,err = sp.communicate()
            return int(out.split()[1])
        except:
            pass
        return None

    def _hide_login_info(opts):
        opts = list(opts)
        for private_opt in ['-p', '--password', '-u', '--username']:
            try:
                i = opts.index(private_opt)
                opts[i+1] = '<PRIVATE>'
            except ValueError:
                pass
        return opts

    max_width = 80
    max_help_position = 80

    # No need to wrap help messages if we're on a wide console
    columns = _find_term_columns()
    if columns: max_width = columns

    fmt = optparse.IndentedHelpFormatter(width=max_width, max_help_position=max_help_position)
    fmt.format_option_strings = _format_option_string

    kw = {
        'version'   : __version__,
        'formatter' : fmt,
        'usage' : '%prog [options] url [url...]',
        'conflict_handler' : 'resolve',
    }

    parser = optparse.OptionParser(**kw)

    # option groups
    general        = optparse.OptionGroup(parser, 'General Options')
    selection      = optparse.OptionGroup(parser, 'Video Selection')
    authentication = optparse.OptionGroup(parser, 'Authentication Options')
    video_format   = optparse.OptionGroup(parser, 'Video Format Options')
    subtitles      = optparse.OptionGroup(parser, 'Subtitle Options')
    downloader     = optparse.OptionGroup(parser, 'Download Options')
    postproc       = optparse.OptionGroup(parser, 'Post-processing Options')
    filesystem     = optparse.OptionGroup(parser, 'Filesystem Options')
    verbosity      = optparse.OptionGroup(parser, 'Verbosity / Simulation Options')

    #general.add_option('-h', '--help',
    #        action='help', help='print this help text and exit')
    #general.add_option('-v', '--version',
    #        action='version', help='print program version and exit')
    #general.add_option('-U', '--update',
    #        action='store_true', dest='update_self', help='update this program to latest version. Make sure that you have sufficient permissions (run with sudo if needed)')
    #general.add_option('-i', '--ignore-errors',
    #        action='store_true', dest='ignoreerrors', help='continue on download errors', default=False)
    #general.add_option('--dump-user-agent',
    #        action='store_true', dest='dump_user_agent',
    #        help='display the current browser identification', default=False)
    #general.add_option('--user-agent',
    #        dest='user_agent', help='specify a custom user agent', metavar='UA')
    #general.add_option('--referer',
    #        dest='referer', help='specify a custom referer, use if the video access is restricted to one domain',
    #        metavar='REF', default=None)
    #general.add_option('--list-extractors',
    #        action='store_true', dest='list_extractors',
    #        help='List all supported extractors and the URLs they would handle', default=False)
    #general.add_option('--extractor-descriptions',
    #        action='store_true', dest='list_extractor_descriptions',
    #        help='Output descriptions of all supported extractors', default=False)
    #general.add_option('--proxy', dest='proxy', default=None, help='Use the specified HTTP/HTTPS proxy', metavar='URL')
    #general.add_option('--no-check-certificate', action='store_true', dest='no_check_certificate', default=False, help='Suppress HTTPS certificate validation.')


    #selection.add_option('--playlist-start',
    #        dest='playliststart', metavar='NUMBER', help='playlist video to start at (default is %default)', default=1)
    #selection.add_option('--playlist-end',
    #        dest='playlistend', metavar='NUMBER', help='playlist video to end at (default is last)', default=-1)
    #selection.add_option('--match-title', dest='matchtitle', metavar='REGEX',help='download only matching titles (regex or caseless sub-string)')
    #selection.add_option('--reject-title', dest='rejecttitle', metavar='REGEX',help='skip download for matching titles (regex or caseless sub-string)')
    #selection.add_option('--max-downloads', metavar='NUMBER', dest='max_downloads', help='Abort after downloading NUMBER files', default=None)
    #selection.add_option('--min-filesize', metavar='SIZE', dest='min_filesize', help="Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)", default=None)
    #selection.add_option('--max-filesize', metavar='SIZE', dest='max_filesize', help="Do not download any videos larger than SIZE (e.g. 50k or 44.6m)", default=None)
    #selection.add_option('--date', metavar='DATE', dest='date', help='download only videos uploaded in this date', default=None)
    #selection.add_option('--datebefore', metavar='DATE', dest='datebefore', help='download only videos uploaded before this date', default=None)
    #selection.add_option('--dateafter', metavar='DATE', dest='dateafter', help='download only videos uploaded after this date', default=None)


    #authentication.add_option('-u', '--username',
    #        dest='username', metavar='USERNAME', help='account username')
    #authentication.add_option('-p', '--password',
    #        dest='password', metavar='PASSWORD', help='account password')
    #authentication.add_option('-n', '--netrc',
    #        action='store_true', dest='usenetrc', help='use .netrc authentication data', default=False)
    #authentication.add_option('--video-password',
    #        dest='videopassword', metavar='PASSWORD', help='video password (vimeo only)')


    #video_format.add_option('-f', '--format',
    #        action='store', dest='format', metavar='FORMAT',
    #        help='video format code, specifiy the order of preference using slashes: "-f 22/17/18". "-f mp4" and "-f flv" are also supported')
    #video_format.add_option('--all-formats',
    #        action='store_const', dest='format', help='download all available video formats', const='all')
    #video_format.add_option('--prefer-free-formats',
    #        action='store_true', dest='prefer_free_formats', default=False, help='prefer free video formats unless a specific one is requested')
    #video_format.add_option('--max-quality',
    #        action='store', dest='format_limit', metavar='FORMAT', help='highest quality format to download')
    #video_format.add_option('-F', '--list-formats',
    #        action='store_true', dest='listformats', help='list all available formats (currently youtube only)')

    #subtitles.add_option('--write-sub', '--write-srt',
    #        action='store_true', dest='writesubtitles',
    #        help='write subtitle file', default=False)
    #subtitles.add_option('--write-auto-sub', '--write-automatic-sub',
    #        action='store_true', dest='writeautomaticsub',
    #        help='write automatic subtitle file (youtube only)', default=False)
    #subtitles.add_option('--all-subs',
    #        action='store_true', dest='allsubtitles',
    #        help='downloads all the available subtitles of the video', default=False)
    #subtitles.add_option('--list-subs',
    #        action='store_true', dest='listsubtitles',
    #        help='lists all available subtitles for the video', default=False)
    #subtitles.add_option('--sub-format',
    #        action='store', dest='subtitlesformat', metavar='FORMAT',
    #        help='subtitle format (default=srt) ([sbv/vtt] youtube only)', default='srt')
    #subtitles.add_option('--sub-lang', '--sub-langs', '--srt-lang',
    #        action='callback', dest='subtitleslangs', metavar='LANGS', type='str',
    #        default=[], callback=_comma_separated_values_options_callback,
    #        help='languages of the subtitles to download (optional) separated by commas, use IETF language tags like \'en,pt\'')

    #downloader.add_option('-r', '--rate-limit',
    #        dest='ratelimit', metavar='LIMIT', help='maximum download rate (e.g. 50k or 44.6m)')
    #downloader.add_option('-R', '--retries',
    #        dest='retries', metavar='RETRIES', help='number of retries (default is %default)', default=10)
    #downloader.add_option('--buffer-size',
    #        dest='buffersize', metavar='SIZE', help='size of download buffer (e.g. 1024 or 16k) (default is %default)', default="1024")
    #downloader.add_option('--no-resize-buffer',
    #        action='store_true', dest='noresizebuffer',
    #        help='do not automatically adjust the buffer size. By default, the buffer size is automatically resized from an initial value of SIZE.', default=False)
    #downloader.add_option('--test', action='store_true', dest='test', default=False, help=optparse.SUPPRESS_HELP)

    #verbosity.add_option('-q', '--quiet',
    #        action='store_true', dest='quiet', help='activates quiet mode', default=False)
    #verbosity.add_option('-s', '--simulate',
    #        action='store_true', dest='simulate', help='do not download the video and do not write anything to disk', default=False)
    #verbosity.add_option('--skip-download',
    #        action='store_true', dest='skip_download', help='do not download the video', default=False)
    #verbosity.add_option('-g', '--get-url',
    #        action='store_true', dest='geturl', help='simulate, quiet but print URL', default=False)
    #verbosity.add_option('-e', '--get-title',
    #        action='store_true', dest='gettitle', help='simulate, quiet but print title', default=False)
    #verbosity.add_option('--get-id',
    #        action='store_true', dest='getid', help='simulate, quiet but print id', default=False)
    #verbosity.add_option('--get-thumbnail',
    #        action='store_true', dest='getthumbnail',
    #        help='simulate, quiet but print thumbnail URL', default=False)
    #verbosity.add_option('--get-description',
    #        action='store_true', dest='getdescription',
    #        help='simulate, quiet but print video description', default=False)
    #verbosity.add_option('--get-filename',
    #        action='store_true', dest='getfilename',
    #        help='simulate, quiet but print output filename', default=False)
    #verbosity.add_option('--get-format',
    #        action='store_true', dest='getformat',
    #        help='simulate, quiet but print output format', default=False)
    #verbosity.add_option('--newline',
    #        action='store_true', dest='progress_with_newline', help='output progress bar as new lines', default=False)
    #verbosity.add_option('--no-progress',
    #        action='store_true', dest='noprogress', help='do not print progress bar', default=False)
    #verbosity.add_option('--console-title',
    #        action='store_true', dest='consoletitle',
    #        help='display progress in console titlebar', default=False)
    #verbosity.add_option('-v', '--verbose',
    #        action='store_true', dest='verbose', help='print various debugging information', default=False)
    #verbosity.add_option('--dump-intermediate-pages',
    #        action='store_true', dest='dump_intermediate_pages', default=False,
    #        help='print downloaded pages to debug problems(very verbose)')

    #filesystem.add_option('-t', '--title',
    #        action='store_true', dest='usetitle', help='use title in file name (default)', default=False)
    #filesystem.add_option('--id',
    #        action='store_true', dest='useid', help='use only video ID in file name', default=False)
    #filesystem.add_option('-l', '--literal',
    #        action='store_true', dest='usetitle', help='[deprecated] alias of --title', default=False)
    #filesystem.add_option('-A', '--auto-number',
    #        action='store_true', dest='autonumber',
    #        help='number downloaded files starting from 00000', default=False)
    #filesystem.add_option('-o', '--output',
    #        dest='outtmpl', metavar='TEMPLATE',
    #        help=('output filename template. Use %(title)s to get the title, '
    #              '%(uploader)s for the uploader name, %(uploader_id)s for the uploader nickname if different, '
    #              '%(autonumber)s to get an automatically incremented number, '
    #              '%(ext)s for the filename extension, %(upload_date)s for the upload date (YYYYMMDD), '
    #              '%(extractor)s for the provider (youtube, metacafe, etc), '
    #              '%(id)s for the video id , %(playlist)s for the playlist the video is in, '
    #              '%(playlist_index)s for the position in the playlist and %% for a literal percent. '
    #              'Use - to output to stdout. Can also be used to download to a different directory, '
    #              'for example with -o \'/my/downloads/%(uploader)s/%(title)s-%(id)s.%(ext)s\' .'))
    #filesystem.add_option('--autonumber-size',
    #        dest='autonumber_size', metavar='NUMBER',
    #        help='Specifies the number of digits in %(autonumber)s when it is present in output filename template or --autonumber option is given')
    #filesystem.add_option('--restrict-filenames',
    #        action='store_true', dest='restrictfilenames',
    #        help='Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames', default=False)
    #filesystem.add_option('-a', '--batch-file',
    #        dest='batchfile', metavar='FILE', help='file containing URLs to download (\'-\' for stdin)')
    #filesystem.add_option('-w', '--no-overwrites',
    #        action='store_true', dest='nooverwrites', help='do not overwrite files', default=False)
    #filesystem.add_option('-c', '--continue',
    #        action='store_true', dest='continue_dl', help='resume partially downloaded files', default=True)
    #filesystem.add_option('--no-continue',
    #        action='store_false', dest='continue_dl',
    #        help='do not resume partially downloaded files (restart from beginning)')
    #filesystem.add_option('--cookies',
    #        dest='cookiefile', metavar='FILE', help='file to read cookies from and dump cookie jar in')
    #filesystem.add_option('--no-part',
    #        action='store_true', dest='nopart', help='do not use .part files', default=False)
    #filesystem.add_option('--no-mtime',
    #        action='store_false', dest='updatetime',
    #        help='do not use the Last-modified header to set the file modification time', default=True)
    #filesystem.add_option('--write-description',
    #        action='store_true', dest='writedescription',
    #        help='write video description to a .description file', default=False)
    #filesystem.add_option('--write-info-json',
    #        action='store_true', dest='writeinfojson',
    #        help='write video metadata to a .info.json file', default=False)
    #filesystem.add_option('--write-thumbnail',
    #        action='store_true', dest='writethumbnail',
    #        help='write thumbnail image to disk', default=False)


    #postproc.add_option('-x', '--extract-audio', action='store_true', dest='extractaudio', default=False,
    #        help='convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)')
    #postproc.add_option('--audio-format', metavar='FORMAT', dest='audioformat', default='best',
    #        help='"best", "aac", "vorbis", "mp3", "m4a", "opus", or "wav"; best by default')
    #postproc.add_option('--audio-quality', metavar='QUALITY', dest='audioquality', default='5',
    #        help='ffmpeg/avconv audio quality specification, insert a value between 0 (better) and 9 (worse) for VBR or a specific bitrate like 128K (default 5)')
    #postproc.add_option('--recode-video', metavar='FORMAT', dest='recodevideo', default=None,
    #        help='Encode the video to another format if necessary (currently supported: mp4|flv|ogg|webm)')
    #postproc.add_option('-k', '--keep-video', action='store_true', dest='keepvideo', default=False,
    #        help='keeps the video file on disk after the post-processing; the video is erased by default')
    #postproc.add_option('--no-post-overwrites', action='store_true', dest='nopostoverwrites', default=False,
    #        help='do not overwrite post-processed files; the post-processed files are overwritten by default')
    postproc.add_option('--embed-subs', action='store_true', dest='embedsubtitles', default=False,
            help='embed subtitles in the video (only for mp4 videos)')


    parser.add_option_group(general)
    parser.add_option_group(selection)
    parser.add_option_group(downloader)
    parser.add_option_group(filesystem)
    parser.add_option_group(verbosity)
    parser.add_option_group(video_format)
    parser.add_option_group(subtitles)
    parser.add_option_group(authentication)
    parser.add_option_group(postproc)

    if overrideArguments is not None:
        opts, args = parser.parse_args(overrideArguments)
        if opts['--verbose']:
            sys.stderr.write(u'[debug] Override config: ' + repr(overrideArguments) + '\n')
    else:
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            userConfFile = os.path.join(xdg_config_home, 'youtube-dl.conf')
        else:
            userConfFile = os.path.join(os.path.expanduser('~'), '.config', 'youtube-dl.conf')
        systemConf = _readOptions('/etc/youtube-dl.conf')
        userConf = _readOptions(userConfFile)
        commandLineConf = sys.argv[1:]
        argv = systemConf + userConf + commandLineConf
        opts, args = parser.parse_args(argv)
        if opts['--verbose']:
            sys.stderr.write(u'[debug] System config: ' + repr(_hide_login_info(systemConf)) + '\n')
            sys.stderr.write(u'[debug] User config: ' + repr(_hide_login_info(userConf)) + '\n')
            sys.stderr.write(u'[debug] Command-line args: ' + repr(_hide_login_info(commandLineConf)) + '\n')

    return parser, opts, args

def _real_main(argv=None):
    # Compatibility fixes for Windows
    if sys.platform == 'win32':
        # https://github.com/rg3/youtube-dl/issues/820
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    opts = docopt(__doc__, version='0.0.1')
    #Support both --title and deprecated --literal
    if not opts['--title']:
        opts['--title'] = opts['--literal']
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

    #parser, opts, args = parseOpts(argv)

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
    all_urls = batchurls + args
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
    #if opts['--netrc'] and (opts['--username'] or opts['--password']):
    #    parser.error(u'using .netrc conflicts with giving username/password')
    if opts['--password'] and not opts['--username']:
        parser.error(u' account username missing\n')
    if opts['--username'] and not opts['--password']:
        opts['--password'] = getpass.getpass(u'Type account password and press return:')

    #if opts['--output'] is not None and (opts['--title'] or opts['--auto-number'] or opts['--id']):
    #    parser.error(u'using output template conflicts with using title, video ID or auto number')
    #if optsopts['--title'] and opts.useid:
    #    parser.error(u'using title conflicts with using video ID')

    if opts['--rate-limit']:
        numeric_limit = FileDownloader.parse_bytes(opts['--rate-limit'])
        if numeric_limit is None:
            parser.error(u'invalid rate limit specified')
        opts['--rate-limit'] = numeric_limit
    if opts['--min-filesize']:
        numeric_limit = FileDownloader.parse_bytes(opts['--min-filesize'])
        if numeric_limit is None:
            parser.error(u'invalid min_filesize specified')
        opts['--min-filesize'] = numeric_limit
    if opts['--max-filesize']:
        numeric_limit = FileDownloader.parse_bytes(opts['--max-filesize'])
        if numeric_limit is None:
            parser.error(u'invalid max_filesize specified')
        opts['--max-filesize'] = numeric_limit
    if opts['--retries'] is not None:  # This should always be true, it has a default
        try:
            opts['--retries'] = int(opts['--retries'])
        except (TypeError, ValueError) as err:
            parser.error(u'invalid retry count specified')
    if opts['--buffer-size'] is not None:  # This should always be true, it has a default
        numeric_buffersize = FileDownloader.parse_bytes(opts['--buffer-size'])
        if numeric_buffersize is None:
            parser.error(u'invalid buffer size specified')
        opts['--buffer-size'] = numeric_buffersize
    try:
        opts['--playlist-start'] = int(opts['--playlist-start'])
        if opts['--playlist-start'] <= 0:
            raise ValueError(u'Playlist start must be positive')
    except (TypeError, ValueError) as err:
        parser.error(u'invalid playlist start number specified')
    try:
        opts['--playlist-end'] = int(opts['--playlist-end'])
        if opts['--playlist-end'] != -1 and (opts['--playlist-end'] <= 0 or opts['--playlist-end'] < opts['--playlist-start']):
            raise ValueError(u'Playlist end must be greater than playlist start')
    except (TypeError, ValueError) as err:
        parser.error(u'invalid playlist end number specified')
    if opts['--extract-audio']:
        if opts['--audio-format'] not in ['best', 'aac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
            parser.error(u'invalid audio format specified')
    if opts['--audio-quality']:
        opts['--audio-quality'] = opts['--audio-quality'].strip('k').strip('K')
        if not opts['--audio-quality'].isdigit():
            parser.error(u'invalid audio quality specified')
    if opts['--recode-video']:
        if opts['--recode-video'] not in ['mp4', 'flv', 'webm', 'ogg']:
            parser.error(u'invalid video recode format specified')
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
            parser.error(u'you must provide at least one URL')
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
        _real_main(argv)
    except DownloadError:
        sys.exit(1)
    except SameFileError:
        sys.exit(u'ERROR: fixed output name but more than one file to download')
    except KeyboardInterrupt:
        sys.exit(u'\nERROR: Interrupted by user')
