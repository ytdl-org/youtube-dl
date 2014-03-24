.. program:: youtube-dl

General Options
---------------
.. option:: -h, --help

    print this help text and exit

.. option:: --version

    print program version and exit

.. option:: -U, --update

    update this program to latest version. Make sure that you have sufficient permissions (run with sudo if needed)

.. option:: -i, --ignore-errors

    continue on download errors, for example to skip unavailable videos in a playlist

.. option:: --abort-on-error

    Abort downloading of further videos (in the playlist or the command line) if an error occurs

.. option:: --dump-user-agent

    display the current browser identification

.. option:: --user-agent <UA>

    specify a custom user agent

.. option:: --referer <REF>

    specify a custom referer, use if the video access is restricted to one domain

.. option:: --add-header <FIELD:VALUE>

    specify a custom HTTP header and its value, separated by a colon ':'. You can use this option multiple times

.. option:: --list-extractors

    List all supported extractors and the URLs they would handle

.. option:: --extractor-descriptions

    Output descriptions of all supported extractors

.. option:: --proxy <URL>

    Use the specified HTTP/HTTPS proxy. Pass in an empty string (--proxy "") for direct connection

.. option:: --no-check-certificate

    Suppress HTTPS certificate validation.

.. option:: --prefer-insecure, --prefer-unsecure

    Use an unencrypted connection to retrieve information about the video. (Currently supported only for YouTube)

.. option:: --cache-dir <DIR>

    Location in the filesystem where youtube-dl can store some downloaded information permanently. By default $XDG_CACHE_HOME/youtube-dl or ~/.cache/youtube-dl . At the moment, only YouTube player files (for videos with obfuscated signatures) are cached, but that may change.

.. option:: --no-cache-dir

    Disable filesystem caching

.. option:: --socket-timeout

    Time to wait before giving up, in seconds

.. option:: --bidi-workaround

    Work around terminals that lack bidirectional text support. Requires bidiv or fribidi executable in PATH

.. option:: --default-search <PREFIX>

    Use this prefix for unqualified URLs. For example "gvsearch2:" downloads two videos from google videos for  youtube-dl "large apple". By default (with value "auto") youtube-dl guesses.

.. option:: --ignore-config

    Do not read configuration files. When given in the global configuration file /etc/youtube-dl.conf: do not read the user configuration in ~/.config/youtube-dl.conf (%APPDATA%/youtube-dl/config.txt on Windows)

.. option:: --encoding <ENCODING>

    Force the specified encoding (experimental)


Video Selection
---------------
.. option:: --playlist-start <NUMBER>

    playlist video to start at (default is %default)

.. option:: --playlist-end <NUMBER>

    playlist video to end at (default is last)

.. option:: --match-title <REGEX>

    download only matching titles (regex or caseless sub-string)

.. option:: --reject-title <REGEX>

    skip download for matching titles (regex or caseless sub-string)

.. option:: --max-downloads <NUMBER>

    Abort after downloading NUMBER files

.. option:: --min-filesize <SIZE>

    Do not download any videos smaller than SIZE (e.g. 50k or 44.6m)

.. option:: --max-filesize <SIZE>

    Do not download any videos larger than SIZE (e.g. 50k or 44.6m)

.. option:: --date <DATE>

    download only videos uploaded in this date

.. option:: --datebefore <DATE>

    download only videos uploaded on or before this date (i.e. inclusive)

.. option:: --dateafter <DATE>

    download only videos uploaded on or after this date (i.e. inclusive)

.. option:: --min-views <COUNT>

    Do not download any videos with less than COUNT views

.. option:: --max-views <COUNT>

    Do not download any videos with more than COUNT views

.. option:: --no-playlist

    download only the currently playing video

.. option:: --age-limit <YEARS>

    download only videos suitable for the given age

.. option:: --download-archive <FILE>

    Download only videos not listed in the archive file. Record the IDs of all downloaded videos in it.

.. option:: --include-ads

    Download advertisements as well (experimental)

.. option:: --youtube-include-dash-manifest

    Try to download the DASH manifest on YouTube videos (experimental)


Download Options
----------------
.. option:: -r, --rate-limit <LIMIT>

    maximum download rate in bytes per second (e.g. 50K or 4.2M)

.. option:: -R, --retries <RETRIES>

    number of retries (default is %default)

.. option:: --buffer-size <SIZE>

    size of download buffer (e.g. 1024 or 16K) (default is %default)

.. option:: --no-resize-buffer

    do not automatically adjust the buffer size. By default, the buffer size is automatically resized from an initial value of SIZE.

.. option:: --test

    SUPPRESSHELP


Filesystem Options
------------------
.. option:: -t, --title

    use title in file name (default)

.. option:: --id

    use only video ID in file name

.. option:: -l, --literal

    [deprecated] alias of --title

.. option:: -A, --auto-number

    number downloaded files starting from 00000

.. option:: -o, --output <TEMPLATE>

    output filename template. Use %(title)s to get the title, %(uploader)s for the uploader name, %(uploader_id)s for the uploader nickname if different, %(autonumber)s to get an automatically incremented number, %(ext)s for the filename extension, %(format)s for the format description (like "22 - 1280x720" or "HD"), %(format_id)s for the unique id of the format (like Youtube's itags: "137"), %(upload_date)s for the upload date (YYYYMMDD), %(extractor)s for the provider (youtube, metacafe, etc), %(id)s for the video id, %(playlist)s for the playlist the video is in, %(playlist_index)s for the position in the playlist and %% for a literal percent. %(height)s and %(width)s for the width and height of the video format. %(resolution)s for a textual description of the resolution of the video format. Use - to output to stdout. Can also be used to download to a different directory, for example with -o '/my/downloads/%(uploader)s/%(title)s-%(id)s.%(ext)s' .

.. option:: --autonumber-size <NUMBER>

    Specifies the number of digits in %(autonumber)s when it is present in output filename template or --auto-number option is given

.. option:: --restrict-filenames

    Restrict filenames to only ASCII characters, and avoid "&" and spaces in filenames

.. option:: -a, --batch-file <FILE>

    file containing URLs to download ('-' for stdin)

.. option:: --load-info <FILE>

    json file containing the video information (created with the "--write-json" option)

.. option:: -w, --no-overwrites

    do not overwrite files

.. option:: -c, --continue

    force resume of partially downloaded files. By default, youtube-dl will resume downloads if possible.

.. option:: --no-continue

    do not resume partially downloaded files (restart from beginning)

.. option:: --cookies <FILE>

    file to read cookies from and dump cookie jar in

.. option:: --no-part

    do not use .part files

.. option:: --no-mtime

    do not use the Last-modified header to set the file modification time

.. option:: --write-description

    write video description to a .description file

.. option:: --write-info-json

    write video metadata to a .info.json file

.. option:: --write-annotations

    write video annotations to a .annotation file

.. option:: --write-thumbnail

    write thumbnail image to disk


Verbosity / Simulation Options
------------------------------
.. option:: -q, --quiet

    activates quiet mode

.. option:: --no-warnings

    Ignore warnings

.. option:: -s, --simulate

    do not download the video and do not write anything to disk

.. option:: --skip-download

    do not download the video

.. option:: -g, --get-url

    simulate, quiet but print URL

.. option:: -e, --get-title

    simulate, quiet but print title

.. option:: --get-id

    simulate, quiet but print id

.. option:: --get-thumbnail

    simulate, quiet but print thumbnail URL

.. option:: --get-description

    simulate, quiet but print video description

.. option:: --get-duration

    simulate, quiet but print video length

.. option:: --get-filename

    simulate, quiet but print output filename

.. option:: --get-format

    simulate, quiet but print output format

.. option:: -j, --dump-json

    simulate, quiet but print JSON information. See --output for a description of available keys.

.. option:: --newline

    output progress bar as new lines

.. option:: --no-progress

    do not print progress bar

.. option:: --console-title

    display progress in console titlebar

.. option:: -v, --verbose

    print various debugging information

.. option:: --dump-intermediate-pages

    print downloaded pages to debug problems (very verbose)

.. option:: --write-pages

    Write downloaded intermediary pages to files in the current directory to debug problems

.. option:: --youtube-print-sig-code

    SUPPRESSHELP

.. option:: --print-traffic

    Display sent and read HTTP traffic


Video Format Options
--------------------
.. option:: -f, --format <FORMAT>

    video format code, specify the order of preference using slashes: "-f 22/17/18". "-f mp4" and "-f flv" are also supported. You can also use the special names "best", "bestvideo", "bestaudio", "worst", "worstvideo" and "worstaudio". By default, youtube-dl will pick the best quality.

.. option:: --all-formats

    download all available video formats

.. option:: --prefer-free-formats

    prefer free video formats unless a specific one is requested

.. option:: --max-quality <FORMAT>

    highest quality format to download

.. option:: -F, --list-formats

    list all available formats


Subtitle Options
----------------
.. option:: --write-sub, --write-srt

    write subtitle file

.. option:: --write-auto-sub, --write-automatic-sub

    write automatic subtitle file (youtube only)

.. option:: --all-subs

    downloads all the available subtitles of the video

.. option:: --list-subs

    lists all available subtitles for the video

.. option:: --sub-format <FORMAT>

    subtitle format (default=srt) ([sbv/vtt] youtube only)

.. option:: --sub-lang, --sub-langs, --srt-lang <LANGS>

    languages of the subtitles to download (optional) separated by commas, use IETF language tags like 'en,pt'


Authentication Options
----------------------
.. option:: -u, --username <USERNAME>

    account username

.. option:: -p, --password <PASSWORD>

    account password

.. option:: -n, --netrc

    use .netrc authentication data

.. option:: --video-password <PASSWORD>

    video password (vimeo, smotri)


Post-processing Options
-----------------------
.. option:: -x, --extract-audio

    convert video files to audio-only files (requires ffmpeg or avconv and ffprobe or avprobe)

.. option:: --audio-format <FORMAT>

    "best", "aac", "vorbis", "mp3", "m4a", "opus", or "wav"; best by default

.. option:: --audio-quality <QUALITY>

    ffmpeg/avconv audio quality specification, insert a value between 0 (better) and 9 (worse) for VBR or a specific bitrate like 128K (default 5)

.. option:: --recode-video <FORMAT>

    Encode the video to another format if necessary (currently supported: mp4|flv|ogg|webm)

.. option:: -k, --keep-video

    keeps the video file on disk after the post-processing; the video is erased by default

.. option:: --no-post-overwrites

    do not overwrite post-processed files; the post-processed files are overwritten by default

.. option:: --embed-subs

    embed subtitles in the video (only for mp4 videos)

.. option:: --add-metadata

    write metadata to the video file

.. option:: --xattrs

    write metadata to the video file's xattrs (using dublin core and xdg standards)

.. option:: --prefer-avconv

    Prefer avconv over ffmpeg for running the postprocessors (default)

.. option:: --prefer-ffmpeg

    Prefer ffmpeg over avconv for running the postprocessors


