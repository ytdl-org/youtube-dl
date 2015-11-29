from __future__ import unicode_literals

import argparse
import sys

from youtube_dl.downloader.external import list_external_downloaders
from youtube_dl.compat import (
    compat_expanduser,
    compat_get_terminal_size,
    compat_getenv,
    compat_kwargs,
    compat_shlex_split,
)
from youtube_dl.utils import (
    preferredencoding,
    write_string,
)
from youtube_dl.version import __version__

from .common import *

def parseOpts(overrideArguments=None):
    parser = argparse.ArgumentParser(usage='%(prog)s [OPTIONS] URL [URL...]')

    general = parser.add_argument_group('General Options')
    general.add_argument('URL', nargs='+')

    general.add_argument(
        '--version',
        action='version', version=__version__,
        help='Print program version and exit')
    general.add_argument(
        '-U', '--update',
        action='store_true', dest='update_self',
        help='Update this program to latest version. Make sure that you have sufficient permissions (run with sudo if needed)')
    general.add_argument(
        '-i', '--ignore-errors',
        action='store_true', dest='ignoreerrors', default=False,
        help='Continue on download errors, for example to skip unavailable videos in a playlist')
    general.add_argument(
        '--abort-on-error',
        action='store_false', dest='ignoreerrors',
        help='Abort downloading of further videos (in the playlist or the command line) if an error occurs')
    general.add_argument(
        '--dump-user-agent',
        action='store_true', dest='dump_user_agent', default=False,
        help='Display the current browser identification')
    general.add_argument(
        '--list-extractors',
        action='store_true', dest='list_extractors', default=False,
        help='List all supported extractors')
    general.add_argument(
        '--extractor-descriptions',
        action='store_true', dest='list_extractor_descriptions', default=False,
        help='Output descriptions of all supported extractors')
    general.add_argument(
        '--force-generic-extractor',
        action='store_true', dest='force_generic_extractor', default=False,
        help='Force extraction to use the generic extractor')
    general.add_argument(
        '--default-search',
        dest='default_search', metavar='PREFIX',
        help='Use this prefix for unqualified URLs. For example "gvsearch2:" downloads two videos from google videos for youtube-dl "large apple". Use the value "auto" to let youtube-dl guess ("auto_warning" to emit a warning when guessing). "error" just throws an error. The default value "fixup_error" repairs broken URLs, but emits an error if this is not possible instead of searching.')
    general.add_argument(
        '--ignore-config',
        action='store_true',
        help='Do not read configuration files. '
        'When given in the global configuration file /etc/youtube-dl.conf: '
        'Do not read the user configuration in ~/.config/youtube-dl/config '
        '(%%APPDATA%%/youtube-dl/config.txt on Windows)')
    general.add_argument(
        '--flat-playlist',
        action='store_const', dest='extract_flat', const='in_playlist',
        default=False,
        help='Do not extract the videos of a playlist, only list them.')
    general.add_argument(
        '--no-color', '--no-colors',
        action='store_true', dest='no_color',
        default=False,
        help='Do not emit color codes in output')

    network = parser.add_argument_group('Network Options')
    network.add_argument(
        '--proxy', dest='proxy', metavar='URL',
        help='Use the specified HTTP/HTTPS proxy. Pass in an empty string (--proxy "") for direct connection')
    network.add_argument(
        '--socket-timeout',
        dest='socket_timeout', type=float, default=None, metavar='SECONDS',
        help='Time to wait before giving up, in seconds')
    network.add_argument(
        '--source-address',
        metavar='IP', dest='source_address', default=None,
        help='Client-side IP address to bind to (experimental)',
    )
    network.add_argument(
        '-4', '--force-ipv4',
        action='store_const', const='0.0.0.0', dest='source_address',
        help='Make all connections via IPv4 (experimental)',
    )
    network.add_argument(
        '-6', '--force-ipv6',
        action='store_const', const='::', dest='source_address',
        help='Make all connections via IPv6 (experimental)',
    )
    network.add_argument(
        '--cn-verification-proxy',
        dest='cn_verification_proxy', default=None, metavar='URL',
        help='Use this proxy to verify the IP address for some Chinese sites. '
        'The default proxy specified by --proxy (or none, if the options is not present) is used for the actual downloading. (experimental)'
    )

    selection = parser.add_argument_group('Video Selection')
    selection.add_argument(
        '--playlist-start',
        dest='playliststart', metavar='NUMBER', default=1, type=int,
        help='Playlist video to start at (default is %(default)s)')
    selection.add_argument(
        '--playlist-end',
        dest='playlistend', metavar='NUMBER', default=None, type=int,
        help='Playlist video to end at (default is last)')
    selection.add_argument(
        '--playlist-items',
        dest='playlist_items', metavar='ITEM_SPEC', default=None,
        help='Playlist video items to download. Specify indices of the videos in the playlist separated by commas like: "--playlist-items 1,2,5,8" if you want to download videos indexed 1, 2, 5, 8 in the playlist. You can specify range: "--playlist-items 1-3,7,10-13", it will download the videos at index 1, 2, 3, 7, 10, 11, 12 and 13.')
    selection.add_argument(
        '--match-title', action='append',
        dest='matchtitle', metavar='REGEX',
        help='Download only matching titles (regex or caseless sub-string)')
    selection.add_argument(
        '--reject-title', action='append',
        dest='rejecttitle', metavar='REGEX',
        help='Skip download for matching titles (regex or caseless sub-string)')
    selection.add_argument(
        '--max-downloads',
        dest='max_downloads', metavar='NUMBER', type=int, default=None,
        help='Abort after downloading NUMBER files')
    selection.add_argument(
        '--min-filesize',
        metavar='SIZE', dest='min_filesize', default=None,
        help='Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)')
    selection.add_argument(
        '--max-filesize',
        metavar='SIZE', dest='max_filesize', default=None,
        help='Do not download any videos larger than SIZE (e.g. 50k or 44.6m)')
    selection.add_argument(
        '--date',
        metavar='DATE', dest='date', default=None,
        help='Download only videos uploaded in this date')
    selection.add_argument(
        '--datebefore',
        metavar='DATE', dest='datebefore', default=None,
        help='Download only videos uploaded on or before this date (i.e. inclusive)')
    selection.add_argument(
        '--dateafter',
        metavar='DATE', dest='dateafter', default=None,
        help='Download only videos uploaded on or after this date (i.e. inclusive)')
    selection.add_argument(
        '--min-views',
        metavar='COUNT', dest='min_views', default=None, type=int,
        help='Do not download any videos with less than COUNT views')
    selection.add_argument(
        '--max-views',
        metavar='COUNT', dest='max_views', default=None, type=int,
        help='Do not download any videos with more than COUNT views')
    selection.add_argument(
        '--match-filter',
        metavar='FILTER', dest='match_filter', default=None,
        help=(
            'Generic video filter (experimental). '
            'Specify any key (see help for -o for a list of available keys) to'
            ' match if the key is present, '
            '!key to check if the key is not present,'
            'key > NUMBER (like "comment_count > 12", also works with '
            '>=, <, <=, !=, =) to compare against a number, and '
            '& to require multiple matches. '
            'Values which are not known are excluded unless you'
            ' put a question mark (?) after the operator.'
            'For example, to only match videos that have been liked more than '
            '100 times and disliked less than 50 times (or the dislike '
            'functionality is not available at the given service), but who '
            'also have a description, use --match-filter '
            '"like_count > 100 & dislike_count <? 50 & description" .'
        ))
    selection.add_argument(
        '--no-playlist',
        action='store_true', dest='noplaylist', default=False,
        help='Download only the video, if the URL refers to a video and a playlist.')
    selection.add_argument(
        '--yes-playlist',
        action='store_false', dest='noplaylist', default=False,
        help='Download the playlist, if the URL refers to a video and a playlist.')
    selection.add_argument(
        '--age-limit',
        metavar='YEARS', dest='age_limit', default=None, type=int,
        help='Download only videos suitable for the given age')
    selection.add_argument(
        '--download-archive', metavar='FILE',
        dest='download_archive',
        help='Download only videos not listed in the archive file. Record the IDs of all downloaded videos in it.')
    selection.add_argument(
        '--include-ads',
        dest='include_ads', action='store_true',
        help='Download advertisements as well (experimental)')

    authentication = parser.add_argument_group('Authentication Options')
    authentication.add_argument(
        '-u', '--username',
        dest='username', metavar='USERNAME',
        help='Login with this account ID')
    authentication.add_argument(
        '-p', '--password',
        dest='password', metavar='PASSWORD',
        help='Account password. If this option is left out, youtube-dl will ask interactively.')
    authentication.add_argument(
        '-2', '--twofactor',
        dest='twofactor', metavar='TWOFACTOR',
        help='Two-factor auth code')
    authentication.add_argument(
        '-n', '--netrc',
        action='store_true', dest='usenetrc', default=False,
        help='Use .netrc authentication data')
    authentication.add_argument(
        '--video-password',
        dest='videopassword', metavar='PASSWORD',
        help='Video password (vimeo, smotri, youku)')

    video_format = parser.add_argument_group('Video Format Options')
    video_format.add_argument(
        '-f', '--format',
        dest='format', metavar='FORMAT', default=None,
        help='Video format code, see the "FORMAT SELECTION" for all the info')
    video_format.add_argument(
        '--all-formats',
        action='store_const', dest='format', const='all',
        help='Download all available video formats')
    video_format.add_argument(
        '--prefer-free-formats',
        action='store_true', dest='prefer_free_formats', default=False,
        help='Prefer free video formats unless a specific one is requested')
    video_format.add_argument(
        '-F', '--list-formats',
        action='store_true', dest='listformats',
        help='List all available formats of requested videos')
    video_format.add_argument(
        '--youtube-include-dash-manifest',
        action='store_true', dest='youtube_include_dash_manifest', default=True,
        help='TODO: suppress help?')
    video_format.add_argument(
        '--youtube-skip-dash-manifest',
        action='store_false', dest='youtube_include_dash_manifest',
        help='Do not download the DASH manifests and related data on YouTube videos')
    video_format.add_argument(
        '--merge-output-format',
        dest='merge_output_format', metavar='FORMAT', default=None,
        help=(
            'If a merge is required (e.g. bestvideo+bestaudio), '
            'output to given container format. One of mkv, mp4, ogg, webm, flv. '
            'Ignored if no merge is required'))

    subtitles = parser.add_argument_group('Subtitle Options')
    subtitles.add_argument(
        '--write-sub', '--write-srt',
        action='store_true', dest='writesubtitles', default=False,
        help='Write subtitle file')
    subtitles.add_argument(
        '--write-auto-sub', '--write-automatic-sub',
        action='store_true', dest='writeautomaticsub', default=False,
        help='Write automatically generated subtitle file (YouTube only)')
    subtitles.add_argument(
        '--all-subs',
        action='store_true', dest='allsubtitles', default=False,
        help='Download all the available subtitles of the video')
    subtitles.add_argument(
        '--list-subs',
        action='store_true', dest='listsubtitles', default=False,
        help='List all available subtitles for the video')
    subtitles.add_argument(
        '--sub-format',
        action='store', dest='subtitlesformat', metavar='FORMAT', default='best',
        help='Subtitle format, accepts formats preference, for example: "srt" or "ass/srt/best"')
    subtitles.add_argument(
        '--sub-lang', '--sub-langs', '--srt-lang',
        dest='subtitleslangs', metavar='LANGS',
        default=[], type=_comma_separated_values_options_callback,
        help='Languages of the subtitles to download (optional) separated by commas, use IETF language tags like \'en,pt\'')

    downloader = parser.add_argument_group('Download Options')
    downloader.add_argument(
        '-r', '--rate-limit',
        dest='ratelimit', metavar='LIMIT',
        help='Maximum download rate in bytes per second (e.g. 50K or 4.2M)')
    downloader.add_argument(
        '-R', '--retries',
        dest='retries', metavar='RETRIES', default=10,
        help='Number of retries (default is %(default)s), or "infinite".')
    downloader.add_argument(
        '--buffer-size',
        dest='buffersize', metavar='SIZE', default='1024',
        help='Size of download buffer (e.g. 1024 or 16K) (default is %(default)s)')
    downloader.add_argument(
        '--no-resize-buffer',
        action='store_true', dest='noresizebuffer', default=False,
        help='Do not automatically adjust the buffer size. By default, the buffer size is automatically resized from an initial value of SIZE.')
    downloader.add_argument(
        '--test',
        action='store_true', dest='test', default=False,
        help=argparse.SUPPRESS)
    downloader.add_argument(
        '--playlist-reverse',
        action='store_true',
        help='Download playlist videos in reverse order')
    downloader.add_argument(
        '--xattr-set-filesize',
        dest='xattr_set_filesize', action='store_true',
        help='Set file xattribute ytdl.filesize with expected filesize (experimental)')
    downloader.add_argument(
        '--hls-prefer-native',
        dest='hls_prefer_native', action='store_true',
        help='Use the native HLS downloader instead of ffmpeg (experimental)')
    downloader.add_argument(
        '--external-downloader',
        dest='external_downloader', metavar='COMMAND',
        help='Use the specified external downloader. '
             'Currently supports %s' % ','.join(list_external_downloaders()))
    downloader.add_argument(
        '--external-downloader-args',
        dest='external_downloader_args', metavar='ARGS',
        help='Give these arguments to the external downloader')

    workarounds = parser.add_argument_group('Workarounds')
    workarounds.add_argument(
        '--encoding',
        dest='encoding', metavar='ENCODING',
        help='Force the specified encoding (experimental)')
    workarounds.add_argument(
        '--no-check-certificate',
        action='store_true', dest='no_check_certificate', default=False,
        help='Suppress HTTPS certificate validation')
    workarounds.add_argument(
        '--prefer-insecure',
        '--prefer-unsecure', action='store_true', dest='prefer_insecure',
        help='Use an unencrypted connection to retrieve information about the video. (Currently supported only for YouTube)')
    workarounds.add_argument(
        '--user-agent',
        metavar='UA', dest='user_agent',
        help='Specify a custom user agent')
    workarounds.add_argument(
        '--referer',
        metavar='URL', dest='referer', default=None,
        help='Specify a custom referer, use if the video access is restricted to one domain',
    )
    workarounds.add_argument(
        '--add-header',
        metavar='FIELD:VALUE', dest='headers', action='append',
        help='Specify a custom HTTP header and its value, separated by a colon \':\'. You can use this option multiple times',
    )
    workarounds.add_argument(
        '--bidi-workaround',
        dest='bidi_workaround', action='store_true',
        help='Work around terminals that lack bidirectional text support. Requires bidiv or fribidi executable in PATH')
    workarounds.add_argument(
        '--sleep-interval', metavar='SECONDS',
        dest='sleep_interval', type=float,
        help='Number of seconds to sleep before each download.')

    verbosity = parser.add_argument_group('Verbosity / Simulation Options')
    verbosity.add_argument(
        '-q', '--quiet',
        action='store_true', dest='quiet', default=False,
        help='Activate quiet mode')
    verbosity.add_argument(
        '--no-warnings',
        dest='no_warnings', action='store_true', default=False,
        help='Ignore warnings')
    verbosity.add_argument(
        '-s', '--simulate',
        action='store_true', dest='simulate', default=False,
        help='Do not download the video and do not write anything to disk')
    verbosity.add_argument(
        '--skip-download',
        action='store_true', dest='skip_download', default=False,
        help='Do not download the video')
    verbosity.add_argument(
        '-g', '--get-url',
        action='store_true', dest='geturl', default=False,
        help='Simulate, quiet but print URL')
    verbosity.add_argument(
        '-e', '--get-title',
        action='store_true', dest='gettitle', default=False,
        help='Simulate, quiet but print title')
    verbosity.add_argument(
        '--get-id',
        action='store_true', dest='getid', default=False,
        help='Simulate, quiet but print id')
    verbosity.add_argument(
        '--get-thumbnail',
        action='store_true', dest='getthumbnail', default=False,
        help='Simulate, quiet but print thumbnail URL')
    verbosity.add_argument(
        '--get-description',
        action='store_true', dest='getdescription', default=False,
        help='Simulate, quiet but print video description')
    verbosity.add_argument(
        '--get-duration',
        action='store_true', dest='getduration', default=False,
        help='Simulate, quiet but print video length')
    verbosity.add_argument(
        '--get-filename',
        action='store_true', dest='getfilename', default=False,
        help='Simulate, quiet but print output filename')
    verbosity.add_argument(
        '--get-format',
        action='store_true', dest='getformat', default=False,
        help='Simulate, quiet but print output format')
    verbosity.add_argument(
        '-j', '--dump-json',
        action='store_true', dest='dumpjson', default=False,
        help='Simulate, quiet but print JSON information. See --output for a description of available keys.')
    verbosity.add_argument(
        '-J', '--dump-single-json',
        action='store_true', dest='dump_single_json', default=False,
        help='Simulate, quiet but print JSON information for each command-line argument. If the URL refers to a playlist, dump the whole playlist information in a single line.')
    verbosity.add_argument(
        '--print-json',
        action='store_true', dest='print_json', default=False,
        help='Be quiet and print the video information as JSON (video is still being downloaded).',
    )
    verbosity.add_argument(
        '--newline',
        action='store_true', dest='progress_with_newline', default=False,
        help='Output progress bar as new lines')
    verbosity.add_argument(
        '--no-progress',
        action='store_true', dest='noprogress', default=False,
        help='Do not print progress bar')
    verbosity.add_argument(
        '--console-title',
        action='store_true', dest='consoletitle', default=False,
        help='Display progress in console titlebar')
    verbosity.add_argument(
        '-v', '--verbose',
        action='store_true', dest='verbose', default=False,
        help='Print various debugging information')
    verbosity.add_argument(
        '--dump-pages', '--dump-intermediate-pages',
        action='store_true', dest='dump_intermediate_pages', default=False,
        help='Print downloaded pages encoded using base64 to debug problems (very verbose)')
    verbosity.add_argument(
        '--write-pages',
        action='store_true', dest='write_pages', default=False,
        help='Write downloaded intermediary pages to files in the current directory to debug problems')
    verbosity.add_argument(
        '--youtube-print-sig-code',
        action='store_true', dest='youtube_print_sig_code', default=False,
        help=argparse.SUPPRESS)
    verbosity.add_argument(
        '--print-traffic', '--dump-headers',
        dest='debug_printtraffic', action='store_true', default=False,
        help='Display sent and read HTTP traffic')
    verbosity.add_argument(
        '-C', '--call-home',
        dest='call_home', action='store_true', default=False,
        help='Contact the youtube-dl server for debugging')
    verbosity.add_argument(
        '--no-call-home',
        dest='call_home', action='store_false', default=False,
        help='Do NOT contact the youtube-dl server for debugging')

    filesystem = parser.add_argument_group('Filesystem Options')
    filesystem.add_argument(
        '-a', '--batch-file',
        dest='batchfile', metavar='FILE',
        help='File containing URLs to download (\'-\' for stdin)')
    filesystem.add_argument(
        '--id', default=False,
        action='store_true', dest='useid', help='Use only video ID in file name')
    filesystem.add_argument(
        '-o', '--output',
        dest='outtmpl', metavar='TEMPLATE',
        help=('Output filename template. Use %%(title)s to get the title, '
              '%%(uploader)s for the uploader name, %%(uploader_id)s for the uploader nickname if different, '
              '%%(autonumber)s to get an automatically incremented number, '
              '%%(ext)s for the filename extension, '
              '%%(format)s for the format description (like "22 - 1280x720" or "HD"), '
              '%%(format_id)s for the unique id of the format (like YouTube\'s itags: "137"), '
              '%%(upload_date)s for the upload date (YYYYMMDD), '
              '%%(extractor)s for the provider (youtube, metacafe, etc), '
              '%%(id)s for the video id, '
              '%%(playlist_title)s, %%(playlist_id)s, or %%(playlist)s (=title if present, ID otherwise) for the playlist the video is in, '
              '%%(playlist_index)s for the position in the playlist. '
              '%%(height)s and %%(width)s for the width and height of the video format. '
              '%%(resolution)s for a textual description of the resolution of the video format. '
              '%%%% for a literal percent. '
              'Use - to output to stdout. Can also be used to download to a different directory, '
              'for example with -o \'/my/downloads/%%(uploader)s/%%(title)s-%%(id)s.%%(ext)s\' .'))
    filesystem.add_argument(
        '--autonumber-size',
        dest='autonumber_size', metavar='NUMBER',
        help='Specify the number of digits in %%(autonumber)s when it is present in output filename template or --auto-number option is given')
    filesystem.add_argument(
        '--restrict-filenames',
        action='store_true', dest='restrictfilenames', default=False,
        help='Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames')
    filesystem.add_argument(
        '-A', '--auto-number',
        action='store_true', dest='autonumber', default=False,
        help='[deprecated; use -o "%%(autonumber)s-%%(title)s.%%(ext)s" ] Number downloaded files starting from 00000')
    filesystem.add_argument(
        '-t', '--title',
        action='store_true', dest='usetitle', default=False,
        help='[deprecated] Use title in file name (default)')
    filesystem.add_argument(
        '-l', '--literal', default=False,
        action='store_true', dest='usetitle',
        help='[deprecated] Alias of --title')
    filesystem.add_argument(
        '-w', '--no-overwrites',
        action='store_true', dest='nooverwrites', default=False,
        help='Do not overwrite files')
    filesystem.add_argument(
        '-c', '--continue',
        action='store_true', dest='continue_dl', default=True,
        help='Force resume of partially downloaded files. By default, youtube-dl will resume downloads if possible.')
    filesystem.add_argument(
        '--no-continue',
        action='store_false', dest='continue_dl',
        help='Do not resume partially downloaded files (restart from beginning)')
    filesystem.add_argument(
        '--no-part',
        action='store_true', dest='nopart', default=False,
        help='Do not use .part files - write directly into output file')
    filesystem.add_argument(
        '--no-mtime',
        action='store_false', dest='updatetime', default=True,
        help='Do not use the Last-modified header to set the file modification time')
    filesystem.add_argument(
        '--write-description',
        action='store_true', dest='writedescription', default=False,
        help='Write video description to a .description file')
    filesystem.add_argument(
        '--write-info-json',
        action='store_true', dest='writeinfojson', default=False,
        help='Write video metadata to a .info.json file')
    filesystem.add_argument(
        '--write-annotations',
        action='store_true', dest='writeannotations', default=False,
        help='Write video annotations to a .annotations.xml file')
    filesystem.add_argument(
        '--load-info',
        dest='load_info_filename', metavar='FILE',
        help='JSON file containing the video information (created with the "--write-info-json" option)')
    filesystem.add_argument(
        '--cookies',
        dest='cookiefile', metavar='FILE',
        help='File to read cookies from and dump cookie jar in')
    filesystem.add_argument(
        '--cache-dir', dest='cachedir', default=None, metavar='DIR',
        help='Location in the filesystem where youtube-dl can store some downloaded information permanently. By default $XDG_CACHE_HOME/youtube-dl or ~/.cache/youtube-dl . At the moment, only YouTube player files (for videos with obfuscated signatures) are cached, but that may change.')
    filesystem.add_argument(
        '--no-cache-dir', action='store_const', const=False, dest='cachedir',
        help='Disable filesystem caching')
    filesystem.add_argument(
        '--rm-cache-dir',
        action='store_true', dest='rm_cachedir',
        help='Delete all filesystem cache files')

    thumbnail = parser.add_argument_group('Thumbnail images')
    thumbnail.add_argument(
        '--write-thumbnail',
        action='store_true', dest='writethumbnail', default=False,
        help='Write thumbnail image to disk')
    thumbnail.add_argument(
        '--write-all-thumbnails',
        action='store_true', dest='write_all_thumbnails', default=False,
        help='Write all thumbnail image formats to disk')
    thumbnail.add_argument(
        '--list-thumbnails',
        action='store_true', dest='list_thumbnails', default=False,
        help='Simulate and list all available thumbnail formats')

    postproc = parser.add_argument_group('Post-processing Options')
    postproc.add_argument(
        '-x', '--extract-audio',
        action='store_true', dest='extractaudio', default=False,
        help='Convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)')
    postproc.add_argument(
        '--audio-format', metavar='FORMAT', dest='audioformat', default='best',
        help='Specify audio format: "best", "aac", "vorbis", "mp3", "m4a", "opus", or "wav"; "%(default)s" by default')
    postproc.add_argument(
        '--audio-quality', metavar='QUALITY',
        dest='audioquality', default='5',
        help='Specify ffmpeg/avconv audio quality, insert a value between 0 (better) and 9 (worse) for VBR or a specific bitrate like 128K (default %(default)s)')
    postproc.add_argument(
        '--recode-video',
        metavar='FORMAT', dest='recodevideo', default=None,
        help='Encode the video to another format if necessary (currently supported: mp4|flv|ogg|webm|mkv|avi)')
    postproc.add_argument(
        '--postprocessor-args',
        dest='postprocessor_args', metavar='ARGS',
        help='Give these arguments to the postprocessor')
    postproc.add_argument(
        '-k', '--keep-video',
        action='store_true', dest='keepvideo', default=False,
        help='Keep the video file on disk after the post-processing; the video is erased by default')
    postproc.add_argument(
        '--no-post-overwrites',
        action='store_true', dest='nopostoverwrites', default=False,
        help='Do not overwrite post-processed files; the post-processed files are overwritten by default')
    postproc.add_argument(
        '--embed-subs',
        action='store_true', dest='embedsubtitles', default=False,
        help='Embed subtitles in the video (only for mkv and mp4 videos)')
    postproc.add_argument(
        '--embed-thumbnail',
        action='store_true', dest='embedthumbnail', default=False,
        help='Embed thumbnail in the audio as cover art')
    postproc.add_argument(
        '--add-metadata',
        action='store_true', dest='addmetadata', default=False,
        help='Write metadata to the video file')
    postproc.add_argument(
        '--metadata-from-title',
        metavar='FORMAT', dest='metafromtitle',
        help='Parse additional metadata like song title / artist from the video title. '
             'The format syntax is the same as --output, '
             'the parsed parameters replace existing values. '
             'Additional templates: %%(album)s, %%(artist)s. '
             'Example: --metadata-from-title "%%(artist)s - %%(title)s" matches a title like '
             '"Coldplay - Paradise"')
    postproc.add_argument(
        '--xattrs',
        action='store_true', dest='xattrs', default=False,
        help='Write metadata to the video file\'s xattrs (using dublin core and xdg standards)')
    postproc.add_argument(
        '--fixup',
        metavar='POLICY', dest='fixup', default='detect_or_warn',
        help='Automatically correct known faults of the file. '
             'One of never (do nothing), warn (only emit a warning), '
             'detect_or_warn (the default; fix file if we can, warn otherwise)')
    postproc.add_argument(
        '--prefer-avconv',
        action='store_false', dest='prefer_ffmpeg',
        help='Prefer avconv over ffmpeg for running the postprocessors (default)')
    postproc.add_argument(
        '--prefer-ffmpeg',
        action='store_true', dest='prefer_ffmpeg',
        help='Prefer ffmpeg over avconv for running the postprocessors')
    postproc.add_argument(
        '--ffmpeg-location', '--avconv-location', metavar='PATH',
        dest='ffmpeg_location',
        help='Location of the ffmpeg/avconv binary; either the path to the binary or its containing directory.')
    postproc.add_argument(
        '--exec',
        metavar='CMD', dest='exec_cmd',
        help='Execute a command on the file after downloading, similar to find\'s -exec syntax. Example: --exec \'adb push {} /sdcard/Music/ && rm {}\'')
    postproc.add_argument(
        '--convert-subtitles', '--convert-subs',
        metavar='FORMAT', dest='convertsubtitles', default=None,
        help='Convert the subtitles to other format (currently supported: srt|ass|vtt)')

    if overrideArguments is not None:
        args = parser.parse_args(overrideArguments)
        if args.verbose:
            write_string('[debug] Override config: ' + repr(overrideArguments) + '\n')
    else:
        def compat_conf(conf):
            if sys.version_info < (3,):
                return [a.decode(preferredencoding(), 'replace') for a in conf]
            return conf

        command_line_conf = compat_conf(sys.argv[1:])

        if '--ignore-config' in command_line_conf:
            system_conf = []
            user_conf = []
        else:
            system_conf = compat_conf(_readOptions('/etc/youtube-dl.conf'))
            if '--ignore-config' in system_conf:
                user_conf = []
            else:
                user_conf = compat_conf(_readUserConf())
        argv = system_conf + user_conf + command_line_conf

        args = parser.parse_args(argv)
        if args.verbose:
            write_string('[debug] System config: ' + repr(_hide_login_info(system_conf)) + '\n')
            write_string('[debug] User config: ' + repr(_hide_login_info(user_conf)) + '\n')
            write_string('[debug] Command-line args: ' + repr(_hide_login_info(command_line_conf)) + '\n')

    return parser, args, args
