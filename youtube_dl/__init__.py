#!/usr/bin/env python
# -*- coding: utf-8 -*-

__authors__  = (
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
    'Steffan \'Ruirize\' James',
    'Andras Elso',
    'Jelle van der Waa',
    'Marcin Cieślak',
    'Anton Larionov',
    'Takuya Tsuchida',
    'Sergey M.',
    'Michael Orlitzky',
    'Chris Gahan',
    'Saimadhav Heblikar',
    'Mike Col',
    'Oleg Prutz',
    'pulpe',
    'Andreas Schmitz',
    'Michael Kaiser',
    'Niklas Laxström',
    'David Triendl',
    'Anthony Weems',
    'David Wagner',
    'Juan C. Olivares',
    'Mattias Harrysson',
)

__license__ = 'Public Domain'

import codecs
import io
import locale
import optparse
import os
import random
import re
import shlex
import sys


from .utils import (
    compat_getpass,
    compat_print,
    DateRange,
    decodeOption,
    get_term_width,
    DownloadError,
    get_cachedir,
    MaxDownloadsReached,
    preferredencoding,
    read_batch_urls,
    SameFileError,
    setproctitle,
    std_headers,
    write_string,
)
from .update import update_self
from .FileDownloader import (
    FileDownloader,
)
from .extractor import gen_extractors
from .version import __version__
from .YoutubeDL import YoutubeDL
from .postprocessor import (
    FFmpegMetadataPP,
    FFmpegVideoConvertor,
    FFmpegExtractAudioPP,
    FFmpegEmbedSubtitlePP,
    XAttrMetadataPP,
)


def parseOpts(overrideArguments=None):
    def _readOptions(filename_bytes, default=[]):
        try:
            optionf = open(filename_bytes)
        except IOError:
            return default  # silently skip if file is not present
        try:
            res = []
            for l in optionf:
                res += shlex.split(l, comments=True)
        finally:
            optionf.close()
        return res

    def _readUserConf():
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME')
        if xdg_config_home:
            userConfFile = os.path.join(xdg_config_home, 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(xdg_config_home, 'youtube-dl.conf')
        else:
            userConfFile = os.path.join(os.path.expanduser('~'), '.config', 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(os.path.expanduser('~'), '.config', 'youtube-dl.conf')
        userConf = _readOptions(userConfFile, None)

        if userConf is None:
            appdata_dir = os.environ.get('appdata')
            if appdata_dir:
                userConf = _readOptions(
                    os.path.join(appdata_dir, 'youtube-dl', 'config'),
                    default=None)
                if userConf is None:
                    userConf = _readOptions(
                        os.path.join(appdata_dir, 'youtube-dl', 'config.txt'),
                        default=None)

        if userConf is None:
            userConf = _readOptions(
                os.path.join(os.path.expanduser('~'), 'youtube-dl.conf'),
                default=None)
        if userConf is None:
            userConf = _readOptions(
                os.path.join(os.path.expanduser('~'), 'youtube-dl.conf.txt'),
                default=None)

        if userConf is None:
            userConf = []

        return userConf

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

    def _hide_login_info(opts):
        opts = list(opts)
        for private_opt in ['-p', '--password', '-u', '--username', '--video-password']:
            try:
                i = opts.index(private_opt)
                opts[i+1] = '<PRIVATE>'
            except ValueError:
                pass
        return opts

    max_width = 80
    max_help_position = 80

    # No need to wrap help messages if we're on a wide console
    columns = get_term_width()
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

    general.add_option('-h', '--help',
            action='help', help='print this help text and exit')
    general.add_option('-v', '--version',
            action='version', help='print program version and exit')
    general.add_option('-U', '--update',
            action='store_true', dest='update_self', help='update this program to latest version. Make sure that you have sufficient permissions (run with sudo if needed)')
    general.add_option('-i', '--ignore-errors',
            action='store_true', dest='ignoreerrors', help='continue on download errors, for example to skip unavailable videos in a playlist', default=False)
    general.add_option('--abort-on-error',
            action='store_false', dest='ignoreerrors',
            help='Abort downloading of further videos (in the playlist or the command line) if an error occurs')
    general.add_option('--dump-user-agent',
            action='store_true', dest='dump_user_agent',
            help='display the current browser identification', default=False)
    general.add_option('--user-agent',
            dest='user_agent', help='specify a custom user agent', metavar='UA')
    general.add_option('--referer',
            dest='referer', help='specify a custom referer, use if the video access is restricted to one domain',
            metavar='REF', default=None)
    general.add_option('--list-extractors',
            action='store_true', dest='list_extractors',
            help='List all supported extractors and the URLs they would handle', default=False)
    general.add_option('--extractor-descriptions',
            action='store_true', dest='list_extractor_descriptions',
            help='Output descriptions of all supported extractors', default=False)
    general.add_option(
        '--proxy', dest='proxy', default=None, metavar='URL',
        help='Use the specified HTTP/HTTPS proxy. Pass in an empty string (--proxy "") for direct connection')
    general.add_option('--no-check-certificate', action='store_true', dest='no_check_certificate', default=False, help='Suppress HTTPS certificate validation.')
    general.add_option(
        '--prefer-insecure', action='store_true', dest='prefer_insecure',
        help='Use an unencrypted connection to retrieve information about the video. (Currently supported only for YouTube)')
    general.add_option(
        '--cache-dir', dest='cachedir', default=get_cachedir(), metavar='DIR',
        help='Location in the filesystem where youtube-dl can store some downloaded information permanently. By default $XDG_CACHE_HOME/youtube-dl or ~/.cache/youtube-dl . At the moment, only YouTube player files (for videos with obfuscated signatures) are cached, but that may change.')
    general.add_option(
        '--no-cache-dir', action='store_const', const=None, dest='cachedir',
        help='Disable filesystem caching')
    general.add_option(
        '--socket-timeout', dest='socket_timeout',
        type=float, default=None, help=u'Time to wait before giving up, in seconds')
    general.add_option(
        '--bidi-workaround', dest='bidi_workaround', action='store_true',
        help=u'Work around terminals that lack bidirectional text support. Requires bidiv or fribidi executable in PATH')
    general.add_option('--default-search',
            dest='default_search', metavar='PREFIX',
            help='Use this prefix for unqualified URLs. For example "gvsearch2:" downloads two videos from google videos for  youtube-dl "large apple". By default (with value "auto") youtube-dl guesses.')
    general.add_option(
        '--ignore-config',
        action='store_true',
        help='Do not read configuration files. When given in the global configuration file /etc/youtube-dl.conf: do not read the user configuration in ~/.config/youtube-dl.conf (%APPDATA%/youtube-dl/config.txt on Windows)')

    selection.add_option(
        '--playlist-start',
        dest='playliststart', metavar='NUMBER', default=1, type=int,
        help='playlist video to start at (default is %default)')
    selection.add_option(
        '--playlist-end',
        dest='playlistend', metavar='NUMBER', default=None, type=int,
        help='playlist video to end at (default is last)')
    selection.add_option('--match-title', dest='matchtitle', metavar='REGEX',help='download only matching titles (regex or caseless sub-string)')
    selection.add_option('--reject-title', dest='rejecttitle', metavar='REGEX',help='skip download for matching titles (regex or caseless sub-string)')
    selection.add_option('--max-downloads', metavar='NUMBER',
                         dest='max_downloads', type=int, default=None,
                         help='Abort after downloading NUMBER files')
    selection.add_option('--min-filesize', metavar='SIZE', dest='min_filesize', help="Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)", default=None)
    selection.add_option('--max-filesize', metavar='SIZE', dest='max_filesize', help="Do not download any videos larger than SIZE (e.g. 50k or 44.6m)", default=None)
    selection.add_option('--date', metavar='DATE', dest='date', help='download only videos uploaded in this date', default=None)
    selection.add_option(
        '--datebefore', metavar='DATE', dest='datebefore', default=None,
        help='download only videos uploaded on or before this date (i.e. inclusive)')
    selection.add_option(
        '--dateafter', metavar='DATE', dest='dateafter', default=None,
        help='download only videos uploaded on or after this date (i.e. inclusive)')
    selection.add_option(
        '--min-views', metavar='COUNT', dest='min_views',
        default=None, type=int,
        help="Do not download any videos with less than COUNT views",)
    selection.add_option(
        '--max-views', metavar='COUNT', dest='max_views',
        default=None, type=int,
        help="Do not download any videos with more than COUNT views",)
    selection.add_option('--no-playlist', action='store_true', dest='noplaylist', help='download only the currently playing video', default=False)
    selection.add_option('--age-limit', metavar='YEARS', dest='age_limit',
                         help='download only videos suitable for the given age',
                         default=None, type=int)
    selection.add_option('--download-archive', metavar='FILE',
                         dest='download_archive',
                         help='Download only videos not listed in the archive file. Record the IDs of all downloaded videos in it.')
    selection.add_option(
        '--include-ads', dest='include_ads',
        action='store_true',
        help='Download advertisements as well (experimental)')
    selection.add_option(
        '--youtube-include-dash-manifest', action='store_true',
        dest='youtube_include_dash_manifest', default=False,
        help='Try to download the DASH manifest on YouTube videos (experimental)')

    authentication.add_option('-u', '--username',
            dest='username', metavar='USERNAME', help='account username')
    authentication.add_option('-p', '--password',
            dest='password', metavar='PASSWORD', help='account password')
    authentication.add_option('-n', '--netrc',
            action='store_true', dest='usenetrc', help='use .netrc authentication data', default=False)
    authentication.add_option('--video-password',
            dest='videopassword', metavar='PASSWORD', help='video password (vimeo, smotri)')


    video_format.add_option('-f', '--format',
            action='store', dest='format', metavar='FORMAT', default=None,
            help='video format code, specify the order of preference using slashes: "-f 22/17/18". "-f mp4" and "-f flv" are also supported. You can also use the special names "best", "bestvideo", "bestaudio", "worst", "worstvideo" and "worstaudio". By default, youtube-dl will pick the best quality.')
    video_format.add_option('--all-formats',
            action='store_const', dest='format', help='download all available video formats', const='all')
    video_format.add_option('--prefer-free-formats',
            action='store_true', dest='prefer_free_formats', default=False, help='prefer free video formats unless a specific one is requested')
    video_format.add_option('--max-quality',
            action='store', dest='format_limit', metavar='FORMAT', help='highest quality format to download')
    video_format.add_option('-F', '--list-formats',
            action='store_true', dest='listformats', help='list all available formats')

    subtitles.add_option('--write-sub', '--write-srt',
            action='store_true', dest='writesubtitles',
            help='write subtitle file', default=False)
    subtitles.add_option('--write-auto-sub', '--write-automatic-sub',
            action='store_true', dest='writeautomaticsub',
            help='write automatic subtitle file (youtube only)', default=False)
    subtitles.add_option('--all-subs',
            action='store_true', dest='allsubtitles',
            help='downloads all the available subtitles of the video', default=False)
    subtitles.add_option('--list-subs',
            action='store_true', dest='listsubtitles',
            help='lists all available subtitles for the video', default=False)
    subtitles.add_option('--sub-format',
            action='store', dest='subtitlesformat', metavar='FORMAT',
            help='subtitle format (default=srt) ([sbv/vtt] youtube only)', default='srt')
    subtitles.add_option('--sub-lang', '--sub-langs', '--srt-lang',
            action='callback', dest='subtitleslangs', metavar='LANGS', type='str',
            default=[], callback=_comma_separated_values_options_callback,
            help='languages of the subtitles to download (optional) separated by commas, use IETF language tags like \'en,pt\'')

    downloader.add_option('-r', '--rate-limit',
            dest='ratelimit', metavar='LIMIT', help='maximum download rate in bytes per second (e.g. 50K or 4.2M)')
    downloader.add_option('-R', '--retries',
            dest='retries', metavar='RETRIES', help='number of retries (default is %default)', default=10)
    downloader.add_option('--buffer-size',
            dest='buffersize', metavar='SIZE', help='size of download buffer (e.g. 1024 or 16K) (default is %default)', default="1024")
    downloader.add_option('--no-resize-buffer',
            action='store_true', dest='noresizebuffer',
            help='do not automatically adjust the buffer size. By default, the buffer size is automatically resized from an initial value of SIZE.', default=False)
    downloader.add_option('--test', action='store_true', dest='test', default=False, help=optparse.SUPPRESS_HELP)

    verbosity.add_option('-q', '--quiet',
            action='store_true', dest='quiet', help='activates quiet mode', default=False)
    verbosity.add_option('-s', '--simulate',
            action='store_true', dest='simulate', help='do not download the video and do not write anything to disk', default=False)
    verbosity.add_option('--skip-download',
            action='store_true', dest='skip_download', help='do not download the video', default=False)
    verbosity.add_option('-g', '--get-url',
            action='store_true', dest='geturl', help='simulate, quiet but print URL', default=False)
    verbosity.add_option('-e', '--get-title',
            action='store_true', dest='gettitle', help='simulate, quiet but print title', default=False)
    verbosity.add_option('--get-id',
            action='store_true', dest='getid', help='simulate, quiet but print id', default=False)
    verbosity.add_option('--get-thumbnail',
            action='store_true', dest='getthumbnail',
            help='simulate, quiet but print thumbnail URL', default=False)
    verbosity.add_option('--get-description',
            action='store_true', dest='getdescription',
            help='simulate, quiet but print video description', default=False)
    verbosity.add_option('--get-duration',
            action='store_true', dest='getduration',
            help='simulate, quiet but print video length', default=False)
    verbosity.add_option('--get-filename',
            action='store_true', dest='getfilename',
            help='simulate, quiet but print output filename', default=False)
    verbosity.add_option('--get-format',
            action='store_true', dest='getformat',
            help='simulate, quiet but print output format', default=False)
    verbosity.add_option('-j', '--dump-json',
            action='store_true', dest='dumpjson',
            help='simulate, quiet but print JSON information', default=False)
    verbosity.add_option('--newline',
            action='store_true', dest='progress_with_newline', help='output progress bar as new lines', default=False)
    verbosity.add_option('--no-progress',
            action='store_true', dest='noprogress', help='do not print progress bar', default=False)
    verbosity.add_option('--console-title',
            action='store_true', dest='consoletitle',
            help='display progress in console titlebar', default=False)
    verbosity.add_option('-v', '--verbose',
            action='store_true', dest='verbose', help='print various debugging information', default=False)
    verbosity.add_option('--dump-intermediate-pages',
            action='store_true', dest='dump_intermediate_pages', default=False,
            help='print downloaded pages to debug problems (very verbose)')
    verbosity.add_option('--write-pages',
            action='store_true', dest='write_pages', default=False,
            help='Write downloaded intermediary pages to files in the current directory to debug problems')
    verbosity.add_option('--youtube-print-sig-code',
            action='store_true', dest='youtube_print_sig_code', default=False,
            help=optparse.SUPPRESS_HELP)
    verbosity.add_option('--print-traffic',
            dest='debug_printtraffic', action='store_true', default=False,
            help='Display sent and read HTTP traffic')


    filesystem.add_option('-t', '--title',
            action='store_true', dest='usetitle', help='use title in file name (default)', default=False)
    filesystem.add_option('--id',
            action='store_true', dest='useid', help='use only video ID in file name', default=False)
    filesystem.add_option('-l', '--literal',
            action='store_true', dest='usetitle', help='[deprecated] alias of --title', default=False)
    filesystem.add_option('-A', '--auto-number',
            action='store_true', dest='autonumber',
            help='number downloaded files starting from 00000', default=False)
    filesystem.add_option('-o', '--output',
            dest='outtmpl', metavar='TEMPLATE',
            help=('output filename template. Use %(title)s to get the title, '
                  '%(uploader)s for the uploader name, %(uploader_id)s for the uploader nickname if different, '
                  '%(autonumber)s to get an automatically incremented number, '
                  '%(ext)s for the filename extension, '
                  '%(format)s for the format description (like "22 - 1280x720" or "HD"), '
                  '%(format_id)s for the unique id of the format (like Youtube\'s itags: "137"), '
                  '%(upload_date)s for the upload date (YYYYMMDD), '
                  '%(extractor)s for the provider (youtube, metacafe, etc), '
                  '%(id)s for the video id, %(playlist)s for the playlist the video is in, '
                  '%(playlist_index)s for the position in the playlist and %% for a literal percent. '
                  '%(height)s and %(width)s for the width and height of the video format. '
                  '%(resolution)s for a textual description of the resolution of the video format. '
                  'Use - to output to stdout. Can also be used to download to a different directory, '
                  'for example with -o \'/my/downloads/%(uploader)s/%(title)s-%(id)s.%(ext)s\' .'))
    filesystem.add_option('--autonumber-size',
            dest='autonumber_size', metavar='NUMBER',
            help='Specifies the number of digits in %(autonumber)s when it is present in output filename template or --auto-number option is given')
    filesystem.add_option('--restrict-filenames',
            action='store_true', dest='restrictfilenames',
            help='Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames', default=False)
    filesystem.add_option('-a', '--batch-file',
            dest='batchfile', metavar='FILE', help='file containing URLs to download (\'-\' for stdin)')
    filesystem.add_option('--load-info',
            dest='load_info_filename', metavar='FILE',
            help='json file containing the video information (created with the "--write-json" option)')
    filesystem.add_option('-w', '--no-overwrites',
            action='store_true', dest='nooverwrites', help='do not overwrite files', default=False)
    filesystem.add_option('-c', '--continue',
            action='store_true', dest='continue_dl', help='force resume of partially downloaded files. By default, youtube-dl will resume downloads if possible.', default=True)
    filesystem.add_option('--no-continue',
            action='store_false', dest='continue_dl',
            help='do not resume partially downloaded files (restart from beginning)')
    filesystem.add_option('--cookies',
            dest='cookiefile', metavar='FILE', help='file to read cookies from and dump cookie jar in')
    filesystem.add_option('--no-part',
            action='store_true', dest='nopart', help='do not use .part files', default=False)
    filesystem.add_option('--no-mtime',
            action='store_false', dest='updatetime',
            help='do not use the Last-modified header to set the file modification time', default=True)
    filesystem.add_option('--write-description',
            action='store_true', dest='writedescription',
            help='write video description to a .description file', default=False)
    filesystem.add_option('--write-info-json',
            action='store_true', dest='writeinfojson',
            help='write video metadata to a .info.json file', default=False)
    filesystem.add_option('--write-annotations',
            action='store_true', dest='writeannotations',
            help='write video annotations to a .annotation file', default=False)
    filesystem.add_option('--write-thumbnail',
            action='store_true', dest='writethumbnail',
            help='write thumbnail image to disk', default=False)


    postproc.add_option('-x', '--extract-audio', action='store_true', dest='extractaudio', default=False,
            help='convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)')
    postproc.add_option('--audio-format', metavar='FORMAT', dest='audioformat', default='best',
            help='"best", "aac", "vorbis", "mp3", "m4a", "opus", or "wav"; best by default')
    postproc.add_option('--audio-quality', metavar='QUALITY', dest='audioquality', default='5',
            help='ffmpeg/avconv audio quality specification, insert a value between 0 (better) and 9 (worse) for VBR or a specific bitrate like 128K (default 5)')
    postproc.add_option('--recode-video', metavar='FORMAT', dest='recodevideo', default=None,
            help='Encode the video to another format if necessary (currently supported: mp4|flv|ogg|webm)')
    postproc.add_option('-k', '--keep-video', action='store_true', dest='keepvideo', default=False,
            help='keeps the video file on disk after the post-processing; the video is erased by default')
    postproc.add_option('--no-post-overwrites', action='store_true', dest='nopostoverwrites', default=False,
            help='do not overwrite post-processed files; the post-processed files are overwritten by default')
    postproc.add_option('--embed-subs', action='store_true', dest='embedsubtitles', default=False,
            help='embed subtitles in the video (only for mp4 videos)')
    postproc.add_option('--add-metadata', action='store_true', dest='addmetadata', default=False,
            help='write metadata to the video file')
    postproc.add_option('--xattrs', action='store_true', dest='xattrs', default=False,
            help='write metadata to the video file\'s xattrs (using dublin core and xdg standards)')
    postproc.add_option('--prefer-avconv', action='store_false', dest='prefer_ffmpeg',
        help='Prefer avconv over ffmpeg for running the postprocessors (default)')
    postproc.add_option('--prefer-ffmpeg', action='store_true', dest='prefer_ffmpeg',
        help='Prefer ffmpeg over avconv for running the postprocessors')


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
        if opts.verbose:
            write_string(u'[debug] Override config: ' + repr(overrideArguments) + '\n')
    else:
        commandLineConf = sys.argv[1:]
        if '--ignore-config' in commandLineConf:
            systemConf = []
            userConf = []
        else:
            systemConf = _readOptions('/etc/youtube-dl.conf')
            if '--ignore-config' in systemConf:
                userConf = []
            else:
                userConf = _readUserConf()
        argv = systemConf + userConf + commandLineConf

        opts, args = parser.parse_args(argv)
        if opts.verbose:
            write_string(u'[debug] System config: ' + repr(_hide_login_info(systemConf)) + '\n')
            write_string(u'[debug] User config: ' + repr(_hide_login_info(userConf)) + '\n')
            write_string(u'[debug] Command-line args: ' + repr(_hide_login_info(commandLineConf)) + '\n')
            write_string(u'[debug] Encodings: locale %r, fs %r, out %r, pref: %r\n' %
                         (locale.getpreferredencoding(), sys.getfilesystemencoding(), sys.stdout.encoding, preferredencoding()))

    return parser, opts, args


def _real_main(argv=None):
    # Compatibility fixes for Windows
    if sys.platform == 'win32':
        # https://github.com/rg3/youtube-dl/issues/820
        codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

    setproctitle(u'youtube-dl')

    parser, opts, args = parseOpts(argv)

    # Set user agent
    if opts.user_agent is not None:
        std_headers['User-Agent'] = opts.user_agent

    # Set referer
    if opts.referer is not None:
        std_headers['Referer'] = opts.referer

    # Dump user agent
    if opts.dump_user_agent:
        compat_print(std_headers['User-Agent'])
        sys.exit(0)

    # Batch file verification
    batch_urls = []
    if opts.batchfile is not None:
        try:
            if opts.batchfile == '-':
                batchfd = sys.stdin
            else:
                batchfd = io.open(opts.batchfile, 'r', encoding='utf-8', errors='ignore')
            batch_urls = read_batch_urls(batchfd)
            if opts.verbose:
                write_string(u'[debug] Batch file urls: ' + repr(batch_urls) + u'\n')
        except IOError:
            sys.exit(u'ERROR: batch file could not be read')
    all_urls = batch_urls + args
    all_urls = [url.strip() for url in all_urls]
    _enc = preferredencoding()
    all_urls = [url.decode(_enc, 'ignore') if isinstance(url, bytes) else url for url in all_urls]

    extractors = gen_extractors()

    if opts.list_extractors:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            compat_print(ie.IE_NAME + (' (CURRENTLY BROKEN)' if not ie._WORKING else ''))
            matchedUrls = [url for url in all_urls if ie.suitable(url)]
            for mu in matchedUrls:
                compat_print(u'  ' + mu)
        sys.exit(0)
    if opts.list_extractor_descriptions:
        for ie in sorted(extractors, key=lambda ie: ie.IE_NAME.lower()):
            if not ie._WORKING:
                continue
            desc = getattr(ie, 'IE_DESC', ie.IE_NAME)
            if desc is False:
                continue
            if hasattr(ie, 'SEARCH_KEY'):
                _SEARCHES = (u'cute kittens', u'slithering pythons', u'falling cat', u'angry poodle', u'purple fish', u'running tortoise')
                _COUNTS = (u'', u'5', u'10', u'all')
                desc += u' (Example: "%s%s:%s" )' % (ie.SEARCH_KEY, random.choice(_COUNTS), random.choice(_SEARCHES))
            compat_print(desc)
        sys.exit(0)


    # Conflicting, missing and erroneous options
    if opts.usenetrc and (opts.username is not None or opts.password is not None):
        parser.error(u'using .netrc conflicts with giving username/password')
    if opts.password is not None and opts.username is None:
        parser.error(u'account username missing\n')
    if opts.outtmpl is not None and (opts.usetitle or opts.autonumber or opts.useid):
        parser.error(u'using output template conflicts with using title, video ID or auto number')
    if opts.usetitle and opts.useid:
        parser.error(u'using title conflicts with using video ID')
    if opts.username is not None and opts.password is None:
        opts.password = compat_getpass(u'Type account password and press [Return]: ')
    if opts.ratelimit is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.ratelimit)
        if numeric_limit is None:
            parser.error(u'invalid rate limit specified')
        opts.ratelimit = numeric_limit
    if opts.min_filesize is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.min_filesize)
        if numeric_limit is None:
            parser.error(u'invalid min_filesize specified')
        opts.min_filesize = numeric_limit
    if opts.max_filesize is not None:
        numeric_limit = FileDownloader.parse_bytes(opts.max_filesize)
        if numeric_limit is None:
            parser.error(u'invalid max_filesize specified')
        opts.max_filesize = numeric_limit
    if opts.retries is not None:
        try:
            opts.retries = int(opts.retries)
        except (TypeError, ValueError):
            parser.error(u'invalid retry count specified')
    if opts.buffersize is not None:
        numeric_buffersize = FileDownloader.parse_bytes(opts.buffersize)
        if numeric_buffersize is None:
            parser.error(u'invalid buffer size specified')
        opts.buffersize = numeric_buffersize
    if opts.playliststart <= 0:
        raise ValueError(u'Playlist start must be positive')
    if opts.playlistend not in (-1, None) and opts.playlistend < opts.playliststart:
        raise ValueError(u'Playlist end must be greater than playlist start')
    if opts.extractaudio:
        if opts.audioformat not in ['best', 'aac', 'mp3', 'm4a', 'opus', 'vorbis', 'wav']:
            parser.error(u'invalid audio format specified')
    if opts.audioquality:
        opts.audioquality = opts.audioquality.strip('k').strip('K')
        if not opts.audioquality.isdigit():
            parser.error(u'invalid audio quality specified')
    if opts.recodevideo is not None:
        if opts.recodevideo not in ['mp4', 'flv', 'webm', 'ogg']:
            parser.error(u'invalid video recode format specified')
    if opts.date is not None:
        date = DateRange.day(opts.date)
    else:
        date = DateRange(opts.dateafter, opts.datebefore)
    if opts.default_search not in ('auto', None) and ':' not in opts.default_search:
        parser.error(u'--default-search invalid; did you forget a colon (:) at the end?')

    # Do not download videos when there are audio-only formats
    if opts.extractaudio and not opts.keepvideo and opts.format is None:
        opts.format = 'bestaudio/best'

    # --all-sub automatically sets --write-sub if --write-auto-sub is not given
    # this was the old behaviour if only --all-sub was given.
    if opts.allsubtitles and (opts.writeautomaticsub == False):
        opts.writesubtitles = True

    if sys.version_info < (3,):
        # In Python 2, sys.argv is a bytestring (also note http://bugs.python.org/issue2128 for Windows systems)
        if opts.outtmpl is not None:
            opts.outtmpl = opts.outtmpl.decode(preferredencoding())
    outtmpl =((opts.outtmpl is not None and opts.outtmpl)
            or (opts.format == '-1' and opts.usetitle and u'%(title)s-%(id)s-%(format)s.%(ext)s')
            or (opts.format == '-1' and u'%(id)s-%(format)s.%(ext)s')
            or (opts.usetitle and opts.autonumber and u'%(autonumber)s-%(title)s-%(id)s.%(ext)s')
            or (opts.usetitle and u'%(title)s-%(id)s.%(ext)s')
            or (opts.useid and u'%(id)s.%(ext)s')
            or (opts.autonumber and u'%(autonumber)s-%(id)s.%(ext)s')
            or u'%(title)s-%(id)s.%(ext)s')
    if not os.path.splitext(outtmpl)[1] and opts.extractaudio:
        parser.error(u'Cannot download a video and extract audio into the same'
                     u' file! Use "{0}.%(ext)s" instead of "{0}" as the output'
                     u' template'.format(outtmpl))

    any_printing = opts.geturl or opts.gettitle or opts.getid or opts.getthumbnail or opts.getdescription or opts.getfilename or opts.getformat or opts.getduration or opts.dumpjson
    download_archive_fn = os.path.expanduser(opts.download_archive) if opts.download_archive is not None else opts.download_archive

    ydl_opts = {
        'usenetrc': opts.usenetrc,
        'username': opts.username,
        'password': opts.password,
        'videopassword': opts.videopassword,
        'quiet': (opts.quiet or any_printing),
        'forceurl': opts.geturl,
        'forcetitle': opts.gettitle,
        'forceid': opts.getid,
        'forcethumbnail': opts.getthumbnail,
        'forcedescription': opts.getdescription,
        'forceduration': opts.getduration,
        'forcefilename': opts.getfilename,
        'forceformat': opts.getformat,
        'forcejson': opts.dumpjson,
        'simulate': opts.simulate,
        'skip_download': (opts.skip_download or opts.simulate or any_printing),
        'format': opts.format,
        'format_limit': opts.format_limit,
        'listformats': opts.listformats,
        'outtmpl': outtmpl,
        'autonumber_size': opts.autonumber_size,
        'restrictfilenames': opts.restrictfilenames,
        'ignoreerrors': opts.ignoreerrors,
        'ratelimit': opts.ratelimit,
        'nooverwrites': opts.nooverwrites,
        'retries': opts.retries,
        'buffersize': opts.buffersize,
        'noresizebuffer': opts.noresizebuffer,
        'continuedl': opts.continue_dl,
        'noprogress': opts.noprogress,
        'progress_with_newline': opts.progress_with_newline,
        'playliststart': opts.playliststart,
        'playlistend': opts.playlistend,
        'noplaylist': opts.noplaylist,
        'logtostderr': opts.outtmpl == '-',
        'consoletitle': opts.consoletitle,
        'nopart': opts.nopart,
        'updatetime': opts.updatetime,
        'writedescription': opts.writedescription,
        'writeannotations': opts.writeannotations,
        'writeinfojson': opts.writeinfojson,
        'writethumbnail': opts.writethumbnail,
        'writesubtitles': opts.writesubtitles,
        'writeautomaticsub': opts.writeautomaticsub,
        'allsubtitles': opts.allsubtitles,
        'listsubtitles': opts.listsubtitles,
        'subtitlesformat': opts.subtitlesformat,
        'subtitleslangs': opts.subtitleslangs,
        'matchtitle': decodeOption(opts.matchtitle),
        'rejecttitle': decodeOption(opts.rejecttitle),
        'max_downloads': opts.max_downloads,
        'prefer_free_formats': opts.prefer_free_formats,
        'verbose': opts.verbose,
        'dump_intermediate_pages': opts.dump_intermediate_pages,
        'write_pages': opts.write_pages,
        'test': opts.test,
        'keepvideo': opts.keepvideo,
        'min_filesize': opts.min_filesize,
        'max_filesize': opts.max_filesize,
        'min_views': opts.min_views,
        'max_views': opts.max_views,
        'daterange': date,
        'cachedir': opts.cachedir,
        'youtube_print_sig_code': opts.youtube_print_sig_code,
        'age_limit': opts.age_limit,
        'download_archive': download_archive_fn,
        'cookiefile': opts.cookiefile,
        'nocheckcertificate': opts.no_check_certificate,
        'prefer_insecure': opts.prefer_insecure,
        'proxy': opts.proxy,
        'socket_timeout': opts.socket_timeout,
        'bidi_workaround': opts.bidi_workaround,
        'debug_printtraffic': opts.debug_printtraffic,
        'prefer_ffmpeg': opts.prefer_ffmpeg,
        'include_ads': opts.include_ads,
        'default_search': opts.default_search,
        'youtube_include_dash_manifest': opts.youtube_include_dash_manifest,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.print_debug_header()
        ydl.add_default_info_extractors()

        # PostProcessors
        # Add the metadata pp first, the other pps will copy it
        if opts.addmetadata:
            ydl.add_post_processor(FFmpegMetadataPP())
        if opts.extractaudio:
            ydl.add_post_processor(FFmpegExtractAudioPP(preferredcodec=opts.audioformat, preferredquality=opts.audioquality, nopostoverwrites=opts.nopostoverwrites))
        if opts.recodevideo:
            ydl.add_post_processor(FFmpegVideoConvertor(preferedformat=opts.recodevideo))
        if opts.embedsubtitles:
            ydl.add_post_processor(FFmpegEmbedSubtitlePP(subtitlesformat=opts.subtitlesformat))
        if opts.xattrs:
            ydl.add_post_processor(XAttrMetadataPP())

        # Update version
        if opts.update_self:
            update_self(ydl.to_screen, opts.verbose)

        # Maybe do nothing
        if (len(all_urls) < 1) and (opts.load_info_filename is None):
            if not opts.update_self:
                parser.error(u'you must provide at least one URL')
            else:
                sys.exit()

        try:
            if opts.load_info_filename is not None:
                retcode = ydl.download_with_info_file(opts.load_info_filename)
            else:
                retcode = ydl.download(all_urls)
        except MaxDownloadsReached:
            ydl.to_screen(u'--max-download limit reached, aborting.')
            retcode = 101

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
