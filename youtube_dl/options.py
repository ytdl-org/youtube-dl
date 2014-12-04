from __future__ import unicode_literals

import os.path
import optparse
import shlex
import sys

from .compat import (
    compat_expanduser,
    compat_getenv,
    compat_kwargs,
)
from .utils import (
    get_term_width,
    write_string,
)
from .version import __version__


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
        xdg_config_home = compat_getenv('XDG_CONFIG_HOME')
        if xdg_config_home:
            userConfFile = os.path.join(xdg_config_home, 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(xdg_config_home, 'youtube-dl.conf')
        else:
            userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl', 'config')
            if not os.path.isfile(userConfFile):
                userConfFile = os.path.join(compat_expanduser('~'), '.config', 'youtube-dl.conf')
        userConf = _readOptions(userConfFile, None)

        if userConf is None:
            appdata_dir = compat_getenv('appdata')
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
                os.path.join(compat_expanduser('~'), 'youtube-dl.conf'),
                default=None)
        if userConf is None:
            userConf = _readOptions(
                os.path.join(compat_expanduser('~'), 'youtube-dl.conf.txt'),
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

        if option.takes_value():
            opts.append(' %s' % option.metavar)

        return "".join(opts)

    def _comma_separated_values_options_callback(option, opt_str, value, parser):
        setattr(parser.values, option.dest, value.split(','))

    def _hide_login_info(opts):
        opts = list(opts)
        for private_opt in ['-p', '--password', '-u', '--username', '--video-password']:
            try:
                i = opts.index(private_opt)
                opts[i + 1] = 'PRIVATE'
            except ValueError:
                pass
        return opts

    # No need to wrap help messages if we're on a wide console
    columns = get_term_width()
    max_width = columns if columns else 80
    max_help_position = 80

    fmt = optparse.IndentedHelpFormatter(width=max_width, max_help_position=max_help_position)
    fmt.format_option_strings = _format_option_string

    kw = {
        'version': __version__,
        'formatter': fmt,
        'usage': '%prog [options] url [url...]',
        'conflict_handler': 'resolve',
    }

    parser = optparse.OptionParser(**compat_kwargs(kw))

    general = optparse.OptionGroup(parser, 'General Options')
    general.add_option(
        '-h', '--help',
        action='help',
        help='print this help text and exit')
    general.add_option(
        '-v', '--version',
        action='version',
        help='print program version and exit')
    general.add_option(
        '-U', '--update',
        action='store_true', dest='update_self',
        help='update this program to latest version. Make sure that you have sufficient permissions (run with sudo if needed)')
    general.add_option(
        '-i', '--ignore-errors',
        action='store_true', dest='ignoreerrors', default=False,
        help='continue on download errors, for example to skip unavailable videos in a playlist')
    general.add_option(
        '--abort-on-error',
        action='store_false', dest='ignoreerrors',
        help='Abort downloading of further videos (in the playlist or the command line) if an error occurs')
    general.add_option(
        '--dump-user-agent',
        action='store_true', dest='dump_user_agent', default=False,
        help='display the current browser identification')
    general.add_option(
        '--list-extractors',
        action='store_true', dest='list_extractors', default=False,
        help='List all supported extractors and the URLs they would handle')
    general.add_option(
        '--extractor-descriptions',
        action='store_true', dest='list_extractor_descriptions', default=False,
        help='Output descriptions of all supported extractors')
    general.add_option(
        '--proxy', dest='proxy',
        default=None, metavar='URL',
        help='Use the specified HTTP/HTTPS proxy. Pass in an empty string (--proxy "") for direct connection')
    general.add_option(
        '--socket-timeout',
        dest='socket_timeout', type=float, default=None,
        help='Time to wait before giving up, in seconds')
    general.add_option(
        '--default-search',
        dest='default_search', metavar='PREFIX',
        help='Use this prefix for unqualified URLs. For example "gvsearch2:" downloads two videos from google videos for  youtube-dl "large apple". Use the value "auto" to let youtube-dl guess ("auto_warning" to emit a warning when guessing). "error" just throws an error. The default value "fixup_error" repairs broken URLs, but emits an error if this is not possible instead of searching.')
    general.add_option(
        '--ignore-config',
        action='store_true',
        help='Do not read configuration files. '
        'When given in the global configuration file /etc/youtube-dl.conf: '
        'Do not read the user configuration in ~/.config/youtube-dl/config '
        '(%APPDATA%/youtube-dl/config.txt on Windows)')
    general.add_option(
        '--flat-playlist',
        action='store_const', dest='extract_flat', const='in_playlist',
        default=False,
        help='Do not extract the videos of a playlist, only list them.')

    selection = optparse.OptionGroup(parser, 'Video Selection')
    selection.add_option(
        '--playlist-start',
        dest='playliststart', metavar='NUMBER', default=1, type=int,
        help='playlist video to start at (default is %default)')
    selection.add_option(
        '--playlist-end',
        dest='playlistend', metavar='NUMBER', default=None, type=int,
        help='playlist video to end at (default is last)')
    selection.add_option(
        '--match-title',
        dest='matchtitle', metavar='REGEX',
        help='download only matching titles (regex or caseless sub-string)')
    selection.add_option(
        '--reject-title',
        dest='rejecttitle', metavar='REGEX',
        help='skip download for matching titles (regex or caseless sub-string)')
    selection.add_option(
        '--max-downloads',
        dest='max_downloads', metavar='NUMBER', type=int, default=None,
        help='Abort after downloading NUMBER files')
    selection.add_option(
        '--min-filesize',
        metavar='SIZE', dest='min_filesize', default=None,
        help='Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)')
    selection.add_option(
        '--max-filesize',
        metavar='SIZE', dest='max_filesize', default=None,
        help='Do not download any videos larger than SIZE (e.g. 50k or 44.6m)')
    selection.add_option(
        '--date',
        metavar='DATE', dest='date', default=None,
        help='download only videos uploaded in this date')
    selection.add_option(
        '--datebefore',
        metavar='DATE', dest='datebefore', default=None,
        help='download only videos uploaded on or before this date (i.e. inclusive)')
    selection.add_option(
        '--dateafter',
        metavar='DATE', dest='dateafter', default=None,
        help='download only videos uploaded on or after this date (i.e. inclusive)')
    selection.add_option(
        '--min-views',
        metavar='COUNT', dest='min_views', default=None, type=int,
        help='Do not download any videos with less than COUNT views',)
    selection.add_option(
        '--max-views',
        metavar='COUNT', dest='max_views', default=None, type=int,
        help='Do not download any videos with more than COUNT views')
    selection.add_option(
        '--no-playlist',
        action='store_true', dest='noplaylist', default=False,
        help='If the URL refers to a video and a playlist, download only the video.')
    selection.add_option(
        '--age-limit',
        metavar='YEARS', dest='age_limit', default=None, type=int,
        help='download only videos suitable for the given age')
    selection.add_option(
        '--download-archive', metavar='FILE',
        dest='download_archive',
        help='Download only videos not listed in the archive file. Record the IDs of all downloaded videos in it.')
    selection.add_option(
        '--include-ads',
        dest='include_ads', action='store_true',
        help='Download advertisements as well (experimental)')

    authentication = optparse.OptionGroup(parser, 'Authentication Options')
    authentication.add_option(
        '-u', '--username',
        dest='username', metavar='USERNAME',
        help='login with this account ID')
    authentication.add_option(
        '-p', '--password',
        dest='password', metavar='PASSWORD',
        help='account password')
    authentication.add_option(
        '-2', '--twofactor',
        dest='twofactor', metavar='TWOFACTOR',
        help='two-factor auth code')
    authentication.add_option(
        '-n', '--netrc',
        action='store_true', dest='usenetrc', default=False,
        help='use .netrc authentication data')
    authentication.add_option(
        '--video-password',
        dest='videopassword', metavar='PASSWORD',
        help='video password (vimeo, smotri)')

    video_format = optparse.OptionGroup(parser, 'Video Format Options')
    video_format.add_option(
        '-f', '--format',
        action='store', dest='format', metavar='FORMAT', default=None,
        help=(
            'video format code, specify the order of preference using'
            ' slashes: -f 22/17/18 .  -f mp4 , -f m4a and  -f flv  are also'
            ' supported. You can also use the special names "best",'
            ' "bestvideo", "bestaudio", "worst", "worstvideo" and'
            ' "worstaudio". By default, youtube-dl will pick the best quality.'
            ' Use commas to download multiple audio formats, such as'
            ' -f  136/137/mp4/bestvideo,140/m4a/bestaudio.'
            ' You can merge the video and audio of two formats into a single'
            ' file using -f <video-format>+<audio-format> (requires ffmpeg or'
            ' avconv), for example -f bestvideo+bestaudio.'))
    video_format.add_option(
        '--all-formats',
        action='store_const', dest='format', const='all',
        help='download all available video formats')
    video_format.add_option(
        '--prefer-free-formats',
        action='store_true', dest='prefer_free_formats', default=False,
        help='prefer free video formats unless a specific one is requested')
    video_format.add_option(
        '--max-quality',
        action='store', dest='format_limit', metavar='FORMAT',
        help='highest quality format to download')
    video_format.add_option(
        '-F', '--list-formats',
        action='store_true', dest='listformats',
        help='list all available formats')
    video_format.add_option(
        '--youtube-include-dash-manifest',
        action='store_true', dest='youtube_include_dash_manifest', default=True,
        help=optparse.SUPPRESS_HELP)
    video_format.add_option(
        '--youtube-skip-dash-manifest',
        action='store_false', dest='youtube_include_dash_manifest',
        help='Do not download the DASH manifest on YouTube videos')

    subtitles = optparse.OptionGroup(parser, 'Subtitle Options')
    subtitles.add_option(
        '--write-sub', '--write-srt',
        action='store_true', dest='writesubtitles', default=False,
        help='write subtitle file')
    subtitles.add_option(
        '--write-auto-sub', '--write-automatic-sub',
        action='store_true', dest='writeautomaticsub', default=False,
        help='write automatic subtitle file (youtube only)')
    subtitles.add_option(
        '--all-subs',
        action='store_true', dest='allsubtitles', default=False,
        help='downloads all the available subtitles of the video')
    subtitles.add_option(
        '--list-subs',
        action='store_true', dest='listsubtitles', default=False,
        help='lists all available subtitles for the video')
    subtitles.add_option(
        '--sub-format',
        action='store', dest='subtitlesformat', metavar='FORMAT', default='srt',
        help='subtitle format (default=srt) ([sbv/vtt] youtube only)')
    subtitles.add_option(
        '--sub-lang', '--sub-langs', '--srt-lang',
        action='callback', dest='subtitleslangs', metavar='LANGS', type='str',
        default=[], callback=_comma_separated_values_options_callback,
        help='languages of the subtitles to download (optional) separated by commas, use IETF language tags like \'en,pt\'')

    downloader = optparse.OptionGroup(parser, 'Download Options')
    downloader.add_option(
        '-r', '--rate-limit',
        dest='ratelimit', metavar='LIMIT',
        help='maximum download rate in bytes per second (e.g. 50K or 4.2M)')
    downloader.add_option(
        '-R', '--retries',
        dest='retries', metavar='RETRIES', default=10,
        help='number of retries (default is %default)')
    downloader.add_option(
        '--buffer-size',
        dest='buffersize', metavar='SIZE', default='1024',
        help='size of download buffer (e.g. 1024 or 16K) (default is %default)')
    downloader.add_option(
        '--no-resize-buffer',
        action='store_true', dest='noresizebuffer', default=False,
        help='do not automatically adjust the buffer size. By default, the buffer size is automatically resized from an initial value of SIZE.')
    downloader.add_option(
        '--test',
        action='store_true', dest='test', default=False,
        help=optparse.SUPPRESS_HELP)

    workarounds = optparse.OptionGroup(parser, 'Workarounds')
    workarounds.add_option(
        '--encoding',
        dest='encoding', metavar='ENCODING',
        help='Force the specified encoding (experimental)')
    workarounds.add_option(
        '--no-check-certificate',
        action='store_true', dest='no_check_certificate', default=False,
        help='Suppress HTTPS certificate validation.')
    workarounds.add_option(
        '--prefer-insecure',
        '--prefer-unsecure', action='store_true', dest='prefer_insecure',
        help='Use an unencrypted connection to retrieve information about the video. (Currently supported only for YouTube)')
    workarounds.add_option(
        '--user-agent',
        metavar='UA', dest='user_agent',
        help='specify a custom user agent')
    workarounds.add_option(
        '--referer',
        metavar='URL', dest='referer', default=None,
        help='specify a custom referer, use if the video access is restricted to one domain',
    )
    workarounds.add_option(
        '--add-header',
        metavar='FIELD:VALUE', dest='headers', action='append',
        help='specify a custom HTTP header and its value, separated by a colon \':\'. You can use this option multiple times',
    )
    workarounds.add_option(
        '--bidi-workaround',
        dest='bidi_workaround', action='store_true',
        help='Work around terminals that lack bidirectional text support. Requires bidiv or fribidi executable in PATH')

    verbosity = optparse.OptionGroup(parser, 'Verbosity / Simulation Options')
    verbosity.add_option(
        '-q', '--quiet',
        action='store_true', dest='quiet', default=False,
        help='activates quiet mode')
    verbosity.add_option(
        '--no-warnings',
        dest='no_warnings', action='store_true', default=False,
        help='Ignore warnings')
    verbosity.add_option(
        '-s', '--simulate',
        action='store_true', dest='simulate', default=False,
        help='do not download the video and do not write anything to disk',)
    verbosity.add_option(
        '--skip-download',
        action='store_true', dest='skip_download', default=False,
        help='do not download the video',)
    verbosity.add_option(
        '-g', '--get-url',
        action='store_true', dest='geturl', default=False,
        help='simulate, quiet but print URL')
    verbosity.add_option(
        '-e', '--get-title',
        action='store_true', dest='gettitle', default=False,
        help='simulate, quiet but print title')
    verbosity.add_option(
        '--get-id',
        action='store_true', dest='getid', default=False,
        help='simulate, quiet but print id')
    verbosity.add_option(
        '--get-thumbnail',
        action='store_true', dest='getthumbnail', default=False,
        help='simulate, quiet but print thumbnail URL')
    verbosity.add_option(
        '--get-description',
        action='store_true', dest='getdescription', default=False,
        help='simulate, quiet but print video description')
    verbosity.add_option(
        '--get-duration',
        action='store_true', dest='getduration', default=False,
        help='simulate, quiet but print video length')
    verbosity.add_option(
        '--get-filename',
        action='store_true', dest='getfilename', default=False,
        help='simulate, quiet but print output filename')
    verbosity.add_option(
        '--get-format',
        action='store_true', dest='getformat', default=False,
        help='simulate, quiet but print output format')
    verbosity.add_option(
        '-j', '--dump-json',
        action='store_true', dest='dumpjson', default=False,
        help='simulate, quiet but print JSON information. See --output for a description of available keys.')
    verbosity.add_option(
        '-J', '--dump-single-json',
        action='store_true', dest='dump_single_json', default=False,
        help='simulate, quiet but print JSON information for each command-line argument. If the URL refers to a playlist, dump the whole playlist information in a single line.')
    verbosity.add_option(
        '--newline',
        action='store_true', dest='progress_with_newline', default=False,
        help='output progress bar as new lines')
    verbosity.add_option(
        '--no-progress',
        action='store_true', dest='noprogress', default=False,
        help='do not print progress bar')
    verbosity.add_option(
        '--console-title',
        action='store_true', dest='consoletitle', default=False,
        help='display progress in console titlebar')
    verbosity.add_option(
        '-v', '--verbose',
        action='store_true', dest='verbose', default=False,
        help='print various debugging information')
    verbosity.add_option(
        '--dump-intermediate-pages',
        action='store_true', dest='dump_intermediate_pages', default=False,
        help='print downloaded pages to debug problems (very verbose)')
    verbosity.add_option(
        '--write-pages',
        action='store_true', dest='write_pages', default=False,
        help='Write downloaded intermediary pages to files in the current directory to debug problems')
    verbosity.add_option(
        '--youtube-print-sig-code',
        action='store_true', dest='youtube_print_sig_code', default=False,
        help=optparse.SUPPRESS_HELP)
    verbosity.add_option(
        '--print-traffic',
        dest='debug_printtraffic', action='store_true', default=False,
        help='Display sent and read HTTP traffic')

    filesystem = optparse.OptionGroup(parser, 'Filesystem Options')
    filesystem.add_option(
        '-a', '--batch-file',
        dest='batchfile', metavar='FILE',
        help='file containing URLs to download (\'-\' for stdin)')
    filesystem.add_option(
        '--id', default=False,
        action='store_true', dest='useid', help='use only video ID in file name')
    filesystem.add_option(
        '-A', '--auto-number',
        action='store_true', dest='autonumber', default=False,
        help='number downloaded files starting from 00000')
    filesystem.add_option(
        '-o', '--output',
        dest='outtmpl', metavar='TEMPLATE',
        help=('output filename template. Use %(title)s to get the title, '
              '%(uploader)s for the uploader name, %(uploader_id)s for the uploader nickname if different, '
              '%(autonumber)s to get an automatically incremented number, '
              '%(ext)s for the filename extension, '
              '%(format)s for the format description (like "22 - 1280x720" or "HD"), '
              '%(format_id)s for the unique id of the format (like Youtube\'s itags: "137"), '
              '%(upload_date)s for the upload date (YYYYMMDD), '
              '%(extractor)s for the provider (youtube, metacafe, etc), '
              '%(id)s for the video id, '
              '%(playlist_title)s, %(playlist_id)s, or %(playlist)s (=title if present, ID otherwise) for the playlist the video is in, '
              '%(playlist_index)s for the position in the playlist. '
              '%(height)s and %(width)s for the width and height of the video format. '
              '%(resolution)s for a textual description of the resolution of the video format. '
              '%% for a literal percent. '
              'Use - to output to stdout. Can also be used to download to a different directory, '
              'for example with -o \'/my/downloads/%(uploader)s/%(title)s-%(id)s.%(ext)s\' .'))
    filesystem.add_option(
        '--autonumber-size',
        dest='autonumber_size', metavar='NUMBER',
        help='Specifies the number of digits in %(autonumber)s when it is present in output filename template or --auto-number option is given')
    filesystem.add_option(
        '--restrict-filenames',
        action='store_true', dest='restrictfilenames', default=False,
        help='Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames')
    filesystem.add_option(
        '-t', '--title',
        action='store_true', dest='usetitle', default=False,
        help='[deprecated] use title in file name (default)')
    filesystem.add_option(
        '-l', '--literal', default=False,
        action='store_true', dest='usetitle',
        help='[deprecated] alias of --title')
    filesystem.add_option(
        '-w', '--no-overwrites',
        action='store_true', dest='nooverwrites', default=False,
        help='do not overwrite files')
    filesystem.add_option(
        '-c', '--continue',
        action='store_true', dest='continue_dl', default=True,
        help='force resume of partially downloaded files. By default, youtube-dl will resume downloads if possible.')
    filesystem.add_option(
        '--no-continue',
        action='store_false', dest='continue_dl',
        help='do not resume partially downloaded files (restart from beginning)')
    filesystem.add_option(
        '--no-part',
        action='store_true', dest='nopart', default=False,
        help='do not use .part files - write directly into output file')
    filesystem.add_option(
        '--no-mtime',
        action='store_false', dest='updatetime', default=True,
        help='do not use the Last-modified header to set the file modification time')
    filesystem.add_option(
        '--write-description',
        action='store_true', dest='writedescription', default=False,
        help='write video description to a .description file')
    filesystem.add_option(
        '--write-info-json',
        action='store_true', dest='writeinfojson', default=False,
        help='write video metadata to a .info.json file')
    filesystem.add_option(
        '--write-annotations',
        action='store_true', dest='writeannotations', default=False,
        help='write video annotations to a .annotation file')
    filesystem.add_option(
        '--write-thumbnail',
        action='store_true', dest='writethumbnail', default=False,
        help='write thumbnail image to disk')
    filesystem.add_option(
        '--load-info',
        dest='load_info_filename', metavar='FILE',
        help='json file containing the video information (created with the "--write-json" option)')
    filesystem.add_option(
        '--cookies',
        dest='cookiefile', metavar='FILE',
        help='file to read cookies from and dump cookie jar in')
    filesystem.add_option(
        '--cache-dir', dest='cachedir', default=None, metavar='DIR',
        help='Location in the filesystem where youtube-dl can store some downloaded information permanently. By default $XDG_CACHE_HOME/youtube-dl or ~/.cache/youtube-dl . At the moment, only YouTube player files (for videos with obfuscated signatures) are cached, but that may change.')
    filesystem.add_option(
        '--no-cache-dir', action='store_const', const=False, dest='cachedir',
        help='Disable filesystem caching')
    filesystem.add_option(
        '--rm-cache-dir',
        action='store_true', dest='rm_cachedir',
        help='Delete all filesystem cache files')

    postproc = optparse.OptionGroup(parser, 'Post-processing Options')
    postproc.add_option(
        '-x', '--extract-audio',
        action='store_true', dest='extractaudio', default=False,
        help='convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)')
    postproc.add_option(
        '--audio-format', metavar='FORMAT', dest='audioformat', default='best',
        help='"best", "aac", "vorbis", "mp3", "m4a", "opus", or "wav"; "%default" by default')
    postproc.add_option(
        '--audio-quality', metavar='QUALITY',
        dest='audioquality', default='5',
        help='ffmpeg/avconv audio quality specification, insert a value between 0 (better) and 9 (worse) for VBR or a specific bitrate like 128K (default %default)')
    postproc.add_option(
        '--recode-video',
        metavar='FORMAT', dest='recodevideo', default=None,
        help='Encode the video to another format if necessary (currently supported: mp4|flv|ogg|webm|mkv)')
    postproc.add_option(
        '-k', '--keep-video',
        action='store_true', dest='keepvideo', default=False,
        help='keeps the video file on disk after the post-processing; the video is erased by default')
    postproc.add_option(
        '--no-post-overwrites',
        action='store_true', dest='nopostoverwrites', default=False,
        help='do not overwrite post-processed files; the post-processed files are overwritten by default')
    postproc.add_option(
        '--embed-subs',
        action='store_true', dest='embedsubtitles', default=False,
        help='embed subtitles in the video (only for mp4 videos)')
    postproc.add_option(
        '--embed-thumbnail',
        action='store_true', dest='embedthumbnail', default=False,
        help='embed thumbnail in the audio as cover art')
    postproc.add_option(
        '--add-metadata',
        action='store_true', dest='addmetadata', default=False,
        help='write metadata to the video file')
    postproc.add_option(
        '--xattrs',
        action='store_true', dest='xattrs', default=False,
        help='write metadata to the video file\'s xattrs (using dublin core and xdg standards)')
    postproc.add_option(
        '--prefer-avconv',
        action='store_false', dest='prefer_ffmpeg',
        help='Prefer avconv over ffmpeg for running the postprocessors (default)')
    postproc.add_option(
        '--prefer-ffmpeg',
        action='store_true', dest='prefer_ffmpeg',
        help='Prefer ffmpeg over avconv for running the postprocessors')
    postproc.add_option(
        '--exec',
        metavar='CMD', dest='exec_cmd',
        help='Execute a command on the file after downloading, similar to find\'s -exec syntax. Example: --exec \'adb push {} /sdcard/Music/ && rm {}\'')

    parser.add_option_group(general)
    parser.add_option_group(selection)
    parser.add_option_group(downloader)
    parser.add_option_group(filesystem)
    parser.add_option_group(verbosity)
    parser.add_option_group(workarounds)
    parser.add_option_group(video_format)
    parser.add_option_group(subtitles)
    parser.add_option_group(authentication)
    parser.add_option_group(postproc)

    if overrideArguments is not None:
        opts, args = parser.parse_args(overrideArguments)
        if opts.verbose:
            write_string('[debug] Override config: ' + repr(overrideArguments) + '\n')
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
            write_string('[debug] System config: ' + repr(_hide_login_info(systemConf)) + '\n')
            write_string('[debug] User config: ' + repr(_hide_login_info(userConf)) + '\n')
            write_string('[debug] Command-line args: ' + repr(_hide_login_info(commandLineConf)) + '\n')

    return parser, opts, args
