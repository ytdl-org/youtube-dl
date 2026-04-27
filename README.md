youtube-dl - download videos from youtube.com or other video platforms

- [DESCRIPTION](#description)
- [OPTIONS](#options)
- [CONFIGURATION](#configuration)
- [OUTPUT TEMPLATE](#output-template)
- [FORMAT SELECTION](#format-selection)
- [VIDEO SELECTION](#video-selection)
- [FAQ](#faq)

# DESCRIPTION

    youtube-dl [OPTIONS] URL [URL...]

# OPTIONS
    -h, --help                           Print this help text and exit
    --version                            Print program version and exit
    -i, --ignore-errors                  Continue on download errors, for
                                         example to skip unavailable videos in a
                                         playlist
    --abort-on-error                     Abort downloading of further videos (in
                                         the playlist or the command line) if an
                                         error occurs
    --dump-user-agent                    Display the current browser
                                         identification
    --list-extractors                    List all supported extractors
    --extractor-descriptions             Output descriptions of all supported
                                         extractors
    --default-search PREFIX              Use this prefix for unqualified URLs.
                                         For example "ytsearch2:" downloads two
                                         videos from YouTube for youtube-dl
                                         "large apple". Use the value "auto"
                                         to let youtube-dl guess ("auto_warning"
                                         to emit a warning when guessing).
                                         "error" just throws an error. The
                                         default value "fixup_error" repairs
                                         broken URLs, but emits an error if this
                                         is not possible instead of searching.
    --ignore-config                      Do not read configuration files. When
                                         given in the global configuration file
                                         /etc/youtube-dl.conf: Do not read the
                                         user configuration in
                                         ~/.config/youtube-dl/config
                                         (%APPDATA%/youtube-dl/config.txt on
                                         Windows)
    --config-location PATH               Location of the configuration file;
                                         either the path to the config or its
                                         containing directory.
    --flat-playlist                      Do not extract the videos of a
                                         playlist, only list them.
    --mark-watched                       Mark videos watched (YouTube only)
    --no-mark-watched                    Do not mark videos watched (YouTube
                                         only)
    --no-color                           Do not emit color codes in output

## Network Options:
    --proxy URL                          Use the specified HTTP/HTTPS proxy.
                                         Pass in an empty string (--proxy "")
                                         for direct connection
    --socket-timeout SECONDS             Time to wait before giving up, in
                                         seconds
    --source-address IP                  Client-side IP address to bind to
    -4, --force-ipv4                     Make all connections via IPv4
    -6, --force-ipv6                     Make all connections via IPv6

## Geo Restriction:
    --geo-verification-proxy URL         Use this proxy to verify the IP address
                                         for some geo-restricted sites. The
                                         default proxy specified by --proxy (or
                                         none, if the option is not present) is
                                         used for the actual downloading.
    --geo-bypass                         Bypass geographic restriction via
                                         faking X-Forwarded-For HTTP header
    --no-geo-bypass                      Do not bypass geographic restriction
                                         via faking X-Forwarded-For HTTP header
    --geo-bypass-country CODE            Force bypass geographic restriction
                                         with explicitly provided two-letter ISO
                                         3166-2 country code
    --geo-bypass-ip-block IP_BLOCK       Force bypass geographic restriction
                                         with explicitly provided IP block in
                                         CIDR notation

## Video Selection:
    --playlist-start NUMBER              Playlist video to start at (default is
                                         1)
    --playlist-end NUMBER                Playlist video to end at (default is
                                         last)
    --playlist-items ITEM_SPEC           Playlist video items to download.
                                         Specify indices of the videos in the
                                         playlist separated by commas like: "--
                                         playlist-items 1,2,5,8" if you want to
                                         download videos indexed 1, 2, 5, 8 in
                                         the playlist. You can specify range: "
                                         --playlist-items 1-3,7,10-13", it will
                                         download the videos at index 1, 2, 3,
                                         7, 10, 11, 12 and 13.
    --match-title REGEX                  Download only matching titles (regex or
                                         caseless sub-string)
    --reject-title REGEX                 Skip download for matching titles
                                         (regex or caseless sub-string)
    --max-downloads NUMBER               Abort after downloading NUMBER files
    --min-filesize SIZE                  Do not download any videos smaller than
                                         SIZE (e.g. 50k or 44.6m)
    --max-filesize SIZE                  Do not download any videos larger than
                                         SIZE (e.g. 50k or 44.6m)
    --date DATE                          Download only videos uploaded in this
                                         date
    --datebefore DATE                    Download only videos uploaded on or
                                         before this date (i.e. inclusive)
    --dateafter DATE                     Download only videos uploaded on or
                                         after this date (i.e. inclusive)
    --min-views COUNT                    Do not download any videos with less
                                         than COUNT views
    --max-views COUNT                    Do not download any videos with more
                                         than COUNT views
    --match-filter FILTER                Generic video filter. Specify any key
                                         (see the "OUTPUT TEMPLATE" for a list
                                         of available keys) to match if the key
                                         is present, !key to check if the key is
                                         not present, key > NUMBER (like
                                         "comment_count > 12", also works with
                                         >=, <, <=, !=, =) to compare against a
                                         number, key = 'LITERAL' (like "uploader
                                         = 'Mike Smith'", also works with !=) to
                                         match against a string literal and & to
                                         require multiple matches. Values which
                                         are not known are excluded unless you
                                         put a question mark (?) after the
                                         operator. For example, to only match
                                         videos that have been liked more than
                                         100 times and disliked less than 50
                                         times (or the dislike functionality is
                                         not available at the given service),
                                         but who also have a description, use
                                         --match-filter "like_count > 100 &
                                         dislike_count <? 50 & description" .
    --no-playlist                        Download only the video, if the URL
                                         refers to a video and a playlist.
    --yes-playlist                       Download the playlist, if the URL
                                         refers to a video and a playlist.
    --age-limit YEARS                    Download only videos suitable for the
                                         given age
    --download-archive FILE              Download only videos not listed in the
                                         archive file. Record the IDs of all
                                         downloaded videos in it.

## Download Options:
    -r, --limit-rate RATE                Maximum download rate in bytes per
                                         second (e.g. 50K or 4.2M)
    -R, --retries RETRIES                Number of retries (default is 10), or
                                         "infinite".
    --fragment-retries RETRIES           Number of retries for a fragment
                                         (default is 10), or "infinite" (DASH,
                                         hlsnative and ISM)
    --skip-unavailable-fragments         Skip unavailable fragments (DASH,
                                         hlsnative and ISM)
    --abort-on-unavailable-fragment      Abort downloading when some fragment is
                                         not available
    --keep-fragments                     Keep downloaded fragments on disk after
                                         downloading is finished; fragments are
                                         erased by default
    --buffer-size SIZE                   Size of download buffer (e.g. 1024 or
                                         16K) (default is 1024)
    --no-resize-buffer                   Do not automatically adjust the buffer
                                         size. By default, the buffer size is
                                         automatically resized from an initial
                                         value of SIZE.
    --http-chunk-size SIZE               Size of a chunk for chunk-based HTTP
                                         downloading (e.g. 10485760 or 10M)
                                         (default is disabled). May be useful
                                         for bypassing bandwidth throttling
                                         imposed by a webserver (experimental)
    --playlist-reverse                   Download playlist videos in reverse
                                         order
    --playlist-random                    Download playlist videos in random
                                         order
    --xattr-set-filesize                 Set file xattribute ytdl.filesize with
                                         expected file size
    --hls-prefer-native                  Use the native HLS downloader instead
                                         of ffmpeg
    --hls-prefer-ffmpeg                  Use ffmpeg instead of the native HLS
                                         downloader
    --hls-use-mpegts                     Use the mpegts container for HLS
                                         videos, allowing to play the video
                                         while downloading (some players may not
                                         be able to play it)
    --external-downloader COMMAND        Use the specified external downloader.
                                         Currently supports aria2c,avconv,axel,c
                                         url,ffmpeg,httpie,wget
    --external-downloader-args ARGS      Give these arguments to the external
                                         downloader

## Filesystem Options:
    -a, --batch-file FILE                File containing URLs to download ('-'
                                         for stdin), one URL per line. Lines
                                         starting with '#', ';' or ']' are
                                         considered as comments and ignored.
    --id                                 Use only video ID in file name
    -o, --output TEMPLATE                Output filename template, see the
                                         "OUTPUT TEMPLATE" for all the info
    --output-na-placeholder PLACEHOLDER  Placeholder value for unavailable meta
                                         fields in output filename template
                                         (default is "NA")
    --autonumber-start NUMBER            Specify the start value for
                                         %(autonumber)s (default is 1)
    --restrict-filenames                 Restrict filenames to only ASCII
                                         characters, and avoid "&" and spaces in
                                         filenames
    -w, --no-overwrites                  Do not overwrite files
    -c, --continue                       Force resume of partially downloaded
                                         files. By default, youtube-dl will
                                         resume downloads if possible.
    --no-continue                        Do not resume partially downloaded
                                         files (restart from beginning)
    --no-part                            Do not use .part files - write directly
                                         into output file
    --no-mtime                           Do not use the Last-modified header to
                                         set the file modification time
    --write-description                  Write video description to a
                                         .description file
    --write-info-json                    Write video metadata to a .info.json
                                         file
    --write-annotations                  Write video annotations to a
                                         .annotations.xml file
    --load-info-json FILE                JSON file containing the video
                                         information (created with the "--write-
                                         info-json" option)
    --cookies FILE                       File to read cookies from and dump
                                         cookie jar in
    --cache-dir DIR                      Location in the filesystem where
                                         youtube-dl can store some downloaded
                                         information permanently. By default
                                         $XDG_CACHE_HOME/youtube-dl or
                                         ~/.cache/youtube-dl . At the moment,
                                         only YouTube player files (for videos
                                         with obfuscated signatures) are cached,
                                         but that may change.
    --no-cache-dir                       Disable filesystem caching
    --rm-cache-dir                       Delete all filesystem cache files

## Thumbnail Options:
    --write-thumbnail                    Write thumbnail image to disk
    --write-all-thumbnails               Write all thumbnail image formats to
                                         disk
    --list-thumbnails                    Simulate and list all available
                                         thumbnail formats

## Verbosity / Simulation Options:
    -q, --quiet                          Activate quiet mode
    --no-warnings                        Ignore warnings
    -s, --simulate                       Do not download the video and do not
                                         write anything to disk
    --skip-download                      Do not download the video
    -g, --get-url                        Simulate, quiet but print URL
    -e, --get-title                      Simulate, quiet but print title
    --get-id                             Simulate, quiet but print id
    --get-thumbnail                      Simulate, quiet but print thumbnail URL
    --get-description                    Simulate, quiet but print video
                                         description
    --get-duration                       Simulate, quiet but print video length
    --get-filename                       Simulate, quiet but print output
                                         filename
    --get-format                         Simulate, quiet but print output format
    -j, --dump-json                      Simulate, quiet but print JSON
                                         information. See the "OUTPUT TEMPLATE"
                                         for a description of available keys.
    -J, --dump-single-json               Simulate, quiet but print JSON
                                         information for each command-line
                                         argument. If the URL refers to a
                                         playlist, dump the whole playlist
                                         information in a single line.
    --print-json                         Be quiet and print the video
                                         information as JSON (video is still
                                         being downloaded).
    --newline                            Output progress bar as new lines
    --no-progress                        Do not print progress bar
    --console-title                      Display progress in console titlebar
    -v, --verbose                        Print various debugging information
    --dump-pages                         Print downloaded pages encoded using
                                         base64 to debug problems (very verbose)
    --write-pages                        Write downloaded intermediary pages to
                                         files in the current directory to debug
                                         problems
    --print-traffic                      Display sent and read HTTP traffic
    -C, --call-home                      Contact the youtube-dl server for
                                         debugging
    --no-call-home                       Do NOT contact the youtube-dl server
                                         for debugging

## Workarounds:
    --encoding ENCODING                  Force the specified encoding
                                         (experimental)
    --no-check-certificate               Suppress HTTPS certificate validation
    --prefer-insecure                    Use an unencrypted connection to
                                         retrieve information about the video.
                                         (Currently supported only for YouTube)
    --user-agent UA                      Specify a custom user agent
    --referer URL                        Specify a custom referer, use if the
                                         video access is restricted to one
                                         domain
    --add-header FIELD:VALUE             Specify a custom HTTP header and its
                                         value, separated by a colon ':'. You
                                         can use this option multiple times
    --bidi-workaround                    Work around terminals that lack
                                         bidirectional text support. Requires
                                         bidiv or fribidi executable in PATH
    --sleep-interval SECONDS             Number of seconds to sleep before each
                                         download when used alone or a lower
                                         bound of a range for randomized sleep
                                         before each download (minimum possible
                                         number of seconds to sleep) when used
                                         along with --max-sleep-interval.
    --max-sleep-interval SECONDS         Upper bound of a range for randomized
                                         sleep before each download (maximum
                                         possible number of seconds to sleep).
                                         Must only be used along with --min-
                                         sleep-interval.

## Video Format Options:
    -f, --format FORMAT                  Video format code, see the "FORMAT
                                         SELECTION" for all the info
    --all-formats                        Download all available video formats
    --prefer-free-formats                Prefer free video formats unless a
                                         specific one is requested
    -F, --list-formats                   List all available formats of requested
                                         videos
    --youtube-skip-dash-manifest         Do not download the DASH manifests and
                                         related data on YouTube videos
    --merge-output-format FORMAT         If a merge is required (e.g.
                                         bestvideo+bestaudio), output to given
                                         container format. One of mkv, mp4, ogg,
                                         webm, flv. Ignored if no merge is
                                         required

## Subtitle Options:
    --write-sub                          Write subtitle file
    --write-auto-sub                     Write automatically generated subtitle
                                         file (YouTube only)
    --all-subs                           Download all the available subtitles of
                                         the video
    --list-subs                          List all available subtitles for the
                                         video
    --sub-format FORMAT                  Subtitle format, accepts formats
                                         preference, for example: "srt" or
                                         "ass/srt/best"
    --sub-lang LANGS                     Languages of the subtitles to download
                                         (optional) separated by commas, use
                                         --list-subs for available language tags

## Authentication Options:
    -u, --username USERNAME              Login with this account ID
    -p, --password PASSWORD              Account password. If this option is
                                         left out, youtube-dl will ask
                                         interactively.
    -2, --twofactor TWOFACTOR            Two-factor authentication code
    -n, --netrc                          Use .netrc authentication data
    --video-password PASSWORD            Video password

## Post-processing Options:
    -x, --extract-audio                  Convert video files to audio-only files
                                         (requires ffmpeg/avconv and
                                         ffprobe/avprobe)
    --audio-format FORMAT                Specify audio format: "best", "aac",
                                         "flac", "mp3", "m4a", "opus", "vorbis",
                                         or "wav"; "best" by default; No effect
                                         without -x
    --audio-quality QUALITY              Specify ffmpeg/avconv audio quality,
                                         insert a value between 0 (better) and 9
                                         (worse) for VBR or a specific bitrate
                                         like 128K (default 5)
    --recode-video FORMAT                Encode the video to another format if
                                         necessary (currently supported:
                                         mp4|flv|ogg|webm|mkv|avi)
    --postprocessor-args ARGS            Give these arguments to the
                                         postprocessor
    -k, --keep-video                     Keep the video file on disk after the
                                         post-processing; the video is erased by
                                         default
    --no-post-overwrites                 Do not overwrite post-processed files;
                                         the post-processed files are
                                         overwritten by default
    --embed-subs                         Embed subtitles in the video (only for
                                         mp4, webm and mkv videos)
    --embed-thumbnail                    Embed thumbnail in the audio as cover
                                         art
    --add-metadata                       Write metadata to the video file
    --metadata-from-title FORMAT         Parse additional metadata like song
                                         title / artist from the video title.
                                         The format syntax is the same as
                                         --output. Regular expression with named
                                         capture groups may also be used. The
                                         parsed parameters replace existing
                                         values. Example: --metadata-from-title
                                         "%(artist)s - %(title)s" matches a
                                         title like "Coldplay - Paradise".
                                         Example (regex): --metadata-from-title
                                         "(?P<artist>.+?) - (?P<title>.+)"
    --xattrs                             Write metadata to the video file's
                                         xattrs (using dublin core and xdg
                                         standards)
    --fixup POLICY                       Automatically correct known faults of
                                         the file. One of never (do nothing),
                                         warn (only emit a warning),
                                         detect_or_warn (the default; fix file
                                         if we can, warn otherwise)
    --prefer-avconv                      Prefer avconv over ffmpeg for running
                                         the postprocessors
    --prefer-ffmpeg                      Prefer ffmpeg over avconv for running
                                         the postprocessors (default)
    --ffmpeg-location PATH               Location of the ffmpeg/avconv binary;
                                         either the path to the binary or its
                                         containing directory.
    --exec CMD                           Execute a command on the file after
                                         downloading and post-processing,
                                         similar to find's -exec syntax.
                                         Example: --exec 'adb push {}
                                         /sdcard/Music/ && rm {}'
    --convert-subs FORMAT                Convert the subtitles to other format
                                         (currently supported: srt|ass|vtt|lrc)

# CONFIGURATION

You can configure youtube-dl by placing any supported command line option to a configuration file. On Linux and macOS, the system wide configuration file is located at `/etc/youtube-dl.conf` and the user wide configuration file at `~/.config/youtube-dl/config`. On Windows, the user wide configuration file locations are `%APPDATA%\youtube-dl\config.txt` or `C:\Users\<user name>\youtube-dl.conf`. Note that by default configuration file may not exist so you may need to create it yourself.

For example, with the following configuration file youtube-dl will always extract the audio, not copy the mtime, use a proxy and save all videos under `Movies` directory in your home directory:
```
# Lines starting with # are comments

# Always extract audio
-x

# Do not copy the mtime
--no-mtime

# Use this proxy
--proxy 127.0.0.1:3128

# Save all videos under Movies directory in your home directory
-o ~/Movies/%(title)s.%(ext)s
```

Note that options in configuration file are just the same options aka switches used in regular command line calls thus there **must be no whitespace** after `-` or `--`, e.g. `-o` or `--proxy` but not `- o` or `-- proxy`.

You can use `--ignore-config` if you want to disable the configuration file for a particular youtube-dl run.

You can also use `--config-location` if you want to use custom configuration file for a particular youtube-dl run.

### Authentication with `.netrc` file

You may also want to configure automatic credentials storage for extractors that support authentication (by providing login and password with `--username` and `--password`) in order not to pass credentials as command line arguments on every youtube-dl execution and prevent tracking plain text passwords in the shell command history. You can achieve this using a [`.netrc` file](https://stackoverflow.com/tags/.netrc/info) on a per extractor basis. For that you will need to create a `.netrc` file in your `$HOME` and restrict permissions to read/write by only you:
```
touch $HOME/.netrc
chmod a-rwx,u+rw $HOME/.netrc
```
After that you can add credentials for an extractor in the following format, where *extractor* is the name of the extractor in lowercase:
```
machine <extractor> login <login> password <password>
```
For example:
```
machine youtube login myaccount@gmail.com password my_youtube_password
```
To activate authentication with the `.netrc` file you should pass `--netrc` to youtube-dl or place it in the [configuration file](#configuration).

On Windows you may also need to setup the `%HOME%` environment variable manually. For example:
```
set HOME=%USERPROFILE%
```

# OUTPUT TEMPLATE

The `-o` option allows users to indicate a template for the output file names.

**tl;dr:** [navigate me to examples](#output-template-examples).

The basic usage is not to set any template arguments when downloading a single file, like in `youtube-dl -o funny_video.flv "https://some/video"`. However, it may contain special sequences that will be replaced when downloading each video. The special sequences may be formatted according to [python string formatting operations](https://docs.python.org/2/library/stdtypes.html#string-formatting). For example, `%(NAME)s` or `%(NAME)05d`. To clarify, that is a percent symbol followed by a name in parentheses, followed by formatting operations. Allowed names along with sequence type are:

 - `id` (string): Video identifier
 - `title` (string): Video title
 - `url` (string): Video URL
 - `ext` (string): Video filename extension
 - `alt_title` (string): A secondary title of the video
 - `display_id` (string): An alternative identifier for the video
 - `uploader` (string): Full name of the video uploader
 - `license` (string): License name the video is licensed under
 - `creator` (string): The creator of the video
 - `release_date` (string): The date (YYYYMMDD) when the video was released
 - `timestamp` (numeric): UNIX timestamp of the moment the video became available
 - `upload_date` (string): Video upload date (YYYYMMDD)
 - `uploader_id` (string): Nickname or id of the video uploader
 - `channel` (string): Full name of the channel the video is uploaded on
 - `channel_id` (string): Id of the channel
 - `location` (string): Physical location where the video was filmed
 - `duration` (numeric): Length of the video in seconds
 - `view_count` (numeric): How many users have watched the video on the platform
 - `like_count` (numeric): Number of positive ratings of the video
 - `dislike_count` (numeric): Number of negative ratings of the video
 - `repost_count` (numeric): Number of reposts of the video
 - `average_rating` (numeric): Average rating give by users, the scale used depends on the webpage
 - `comment_count` (numeric): Number of comments on the video
 - `age_limit` (numeric): Age restriction for the video (years)
 - `is_live` (boolean): Whether this video is a live stream or a fixed-length video
 - `start_time` (numeric): Time in seconds where the reproduction should start, as specified in the URL
 - `end_time` (numeric): Time in seconds where the reproduction should end, as specified in the URL
 - `format` (string): A human-readable description of the format
 - `format_id` (string): Format code specified by `--format`
 - `format_note` (string): Additional info about the format
 - `width` (numeric): Width of the video
 - `height` (numeric): Height of the video
 - `resolution` (string): Textual description of width and height
 - `tbr` (numeric): Average bitrate of audio and video in KBit/s
 - `abr` (numeric): Average audio bitrate in KBit/s
 - `acodec` (string): Name of the audio codec in use
 - `asr` (numeric): Audio sampling rate in Hertz
 - `vbr` (numeric): Average video bitrate in KBit/s
 - `fps` (numeric): Frame rate
 - `vcodec` (string): Name of the video codec in use
 - `container` (string): Name of the container format
 - `filesize` (numeric): The number of bytes, if known in advance
 - `filesize_approx` (numeric): An estimate for the number of bytes
 - `protocol` (string): The protocol that will be used for the actual download
 - `extractor` (string): Name of the extractor
 - `extractor_key` (string): Key name of the extractor
 - `epoch` (numeric): Unix epoch when creating the file
 - `autonumber` (numeric): Number that will be increased with each download, starting at `--autonumber-start`
 - `playlist` (string): Name or id of the playlist that contains the video
 - `playlist_index` (numeric): Index of the video in the playlist padded with leading zeros according to the total length of the playlist
 - `playlist_id` (string): Playlist identifier
 - `playlist_title` (string): Playlist title
 - `playlist_uploader` (string): Full name of the playlist uploader
 - `playlist_uploader_id` (string): Nickname or id of the playlist uploader

Available for the video that belongs to some logical chapter or section:

 - `chapter` (string): Name or title of the chapter the video belongs to
 - `chapter_number` (numeric): Number of the chapter the video belongs to
 - `chapter_id` (string): Id of the chapter the video belongs to

Available for the video that is an episode of some series or programme:

 - `series` (string): Title of the series or programme the video episode belongs to
 - `season` (string): Title of the season the video episode belongs to
 - `season_number` (numeric): Number of the season the video episode belongs to
 - `season_id` (string): Id of the season the video episode belongs to
 - `episode` (string): Title of the video episode
 - `episode_number` (numeric): Number of the video episode within a season
 - `episode_id` (string): Id of the video episode

Available for the media that is a track or a part of a music album:

 - `track` (string): Title of the track
 - `track_number` (numeric): Number of the track within an album or a disc
 - `track_id` (string): Id of the track
 - `artist` (string): Artist(s) of the track
 - `genre` (string): Genre(s) of the track
 - `album` (string): Title of the album the track belongs to
 - `album_type` (string): Type of the album
 - `album_artist` (string): List of all artists appeared on the album
 - `disc_number` (numeric): Number of the disc or other physical medium the track belongs to
 - `release_year` (numeric): Year (YYYY) when the album was released

Each aforementioned sequence when referenced in an output template will be replaced by the actual value corresponding to the sequence name. Note that some of the sequences are not guaranteed to be present since they depend on the metadata obtained by a particular extractor. Such sequences will be replaced with placeholder value provided with `--output-na-placeholder` (`NA` by default).

For example for `-o %(title)s-%(id)s.%(ext)s` and an mp4 video with title `youtube-dl test video` and id `BaW_jenozKcj`, this will result in a `youtube-dl test video-BaW_jenozKcj.mp4` file created in the current directory.

For numeric sequences you can use numeric related formatting, for example, `%(view_count)05d` will result in a string with view count padded with zeros up to 5 characters, like in `00042`.

Output templates can also contain arbitrary hierarchical path, e.g. `-o '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'` which will result in downloading each video in a directory corresponding to this path template. Any missing directory will be automatically created for you.

To use percent literals in an output template use `%%`. To output to stdout use `-o -`.

The current default template is `%(title)s-%(id)s.%(ext)s`.

In some cases, you don't want special characters such as 中, spaces, or &, such as when transferring the downloaded filename to a Windows system or the filename through an 8bit-unsafe channel. In these cases, add the `--restrict-filenames` flag to get a shorter title.

#### Output template and Windows batch files

If you are using an output template inside a Windows batch file then you must escape plain percent characters (`%`) by doubling, so that `-o "%(title)s-%(id)s.%(ext)s"` should become `-o "%%(title)s-%%(id)s.%%(ext)s"`. However you should not touch `%`'s that are not plain characters, e.g. environment variables for expansion should stay intact: `-o "C:\%HOMEPATH%\Desktop\%%(title)s.%%(ext)s"`.

#### Output template examples

Note that on Windows you may need to use double quotes instead of single.

```bash
$ youtube-dl --get-filename -o '%(title)s.%(ext)s' BaW_jenozKc
youtube-dl test video ''_ä↭𝕐.mp4    # All kinds of weird characters

$ youtube-dl --get-filename -o '%(title)s.%(ext)s' BaW_jenozKc --restrict-filenames
youtube-dl_test_video_.mp4          # A simple file name

# Download YouTube playlist videos in separate directory indexed by video order in a playlist
$ youtube-dl -o '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s' https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re

# Download all playlists of YouTube channel/user keeping each playlist in separate directory:
$ youtube-dl -o '%(uploader)s/%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s' https://www.youtube.com/user/TheLinuxFoundation/playlists

# Download entire series season keeping each series and each season in separate directory under C:/MyVideos
$ youtube-dl -o "C:/MyVideos/%(series)s/%(season_number)s - %(season)s/%(episode_number)s - %(episode)s.%(ext)s" https://videomore.ru/kino_v_detalayah/5_sezon/367617

# Stream the video being downloaded to stdout
$ youtube-dl -o - BaW_jenozKc
```

# FORMAT SELECTION

By default youtube-dl tries to download the best available quality, i.e. if you want the best quality you **don't need** to pass any special options, youtube-dl will guess it for you by **default**.

But sometimes you may want to download in a different format, for example when you are on a slow or intermittent connection. The key mechanism for achieving this is so-called *format selection* based on which you can explicitly specify desired format, select formats based on some criterion or criteria, setup precedence and much more.

The general syntax for format selection is `--format FORMAT` or shorter `-f FORMAT` where `FORMAT` is a *selector expression*, i.e. an expression that describes format or formats you would like to download.

**tl;dr:** [navigate me to examples](#format-selection-examples).

The simplest case is requesting a specific format, for example with `-f 22` you can download the format with format code equal to 22. You can get the list of available format codes for particular video using `--list-formats` or `-F`. Note that these format codes are extractor specific.

You can also use a file extension (currently `3gp`, `aac`, `flv`, `m4a`, `mp3`, `mp4`, `ogg`, `wav`, `webm` are supported) to download the best quality format of a particular file extension served as a single file, e.g. `-f webm` will download the best quality format with the `webm` extension served as a single file.

You can also use special names to select particular edge case formats:

 - `best`: Select the best quality format represented by a single file with video and audio.
 - `worst`: Select the worst quality format represented by a single file with video and audio.
 - `bestvideo`: Select the best quality video-only format (e.g. DASH video). May not be available.
 - `worstvideo`: Select the worst quality video-only format. May not be available.
 - `bestaudio`: Select the best quality audio only-format. May not be available.
 - `worstaudio`: Select the worst quality audio only-format. May not be available.

For example, to download the worst quality video-only format you can use `-f worstvideo`.

If you want to download multiple videos and they don't have the same formats available, you can specify the order of preference using slashes. Note that slash is left-associative, i.e. formats on the left hand side are preferred, for example `-f 22/17/18` will download format 22 if it's available, otherwise it will download format 17 if it's available, otherwise it will download format 18 if it's available, otherwise it will complain that no suitable formats are available for download.

If you want to download several formats of the same video use a comma as a separator, e.g. `-f 22,17,18` will download all these three formats, of course if they are available. Or a more sophisticated example combined with the precedence feature: `-f 136/137/mp4/bestvideo,140/m4a/bestaudio`.

You can also filter the video formats by putting a condition in brackets, as in `-f "best[height=720]"` (or `-f "[filesize>10M]"`).

The following numeric meta fields can be used with comparisons `<`, `<=`, `>`, `>=`, `=` (equals), `!=` (not equals):

 - `filesize`: The number of bytes, if known in advance
 - `width`: Width of the video, if known
 - `height`: Height of the video, if known
 - `tbr`: Average bitrate of audio and video in KBit/s
 - `abr`: Average audio bitrate in KBit/s
 - `vbr`: Average video bitrate in KBit/s
 - `asr`: Audio sampling rate in Hertz
 - `fps`: Frame rate

Also filtering work for comparisons `=` (equals), `^=` (starts with), `$=` (ends with), `*=` (contains) and following string meta fields:

 - `ext`: File extension
 - `acodec`: Name of the audio codec in use
 - `vcodec`: Name of the video codec in use
 - `container`: Name of the container format
 - `protocol`: The protocol that will be used for the actual download, lower-case (`http`, `https`, `rtsp`, `rtmp`, `rtmpe`, `mms`, `f4m`, `ism`, `http_dash_segments`, `m3u8`, or `m3u8_native`)
 - `format_id`: A short description of the format
 - `language`: Language code

Any string comparison may be prefixed with negation `!` in order to produce an opposite comparison, e.g. `!*=` (does not contain).

Note that none of the aforementioned meta fields are guaranteed to be present since this solely depends on the metadata obtained by particular extractor, i.e. the metadata offered by the video hoster.

Formats for which the value is not known are excluded unless you put a question mark (`?`) after the operator. You can combine format filters, so `-f "[height <=? 720][tbr>500]"` selects up to 720p videos (or videos where the height is not known) with a bitrate of at least 500 KBit/s.

You can merge the video and audio of two formats into a single file using `-f <video-format>+<audio-format>` (requires ffmpeg or avconv installed), for example `-f bestvideo+bestaudio` will download the best video-only format, the best audio-only format and mux them together with ffmpeg/avconv.

Format selectors can also be grouped using parentheses, for example if you want to download the best mp4 and webm formats with a height lower than 480 you can use `-f '(mp4,webm)[height<480]'`.

Since the end of April 2015 and version 2015.04.26, youtube-dl uses `-f bestvideo+bestaudio/best` as the default format selection (see [#5447](https://github.com/ytdl-org/youtube-dl/issues/5447), [#5456](https://github.com/ytdl-org/youtube-dl/issues/5456)). If ffmpeg or avconv are installed this results in downloading `bestvideo` and `bestaudio` separately and muxing them together into a single file giving the best overall quality available. Otherwise it falls back to `best` and results in downloading the best available quality served as a single file. `best` is also needed for videos that don't come from YouTube because they don't provide the audio and video in two different files. If you want to only download some DASH formats (for example if you are not interested in getting videos with a resolution higher than 1080p), you can add `-f bestvideo[height<=?1080]+bestaudio/best` to your configuration file. Note that if you use youtube-dl to stream to `stdout` (and most likely to pipe it to your media player then), i.e. you explicitly specify output template as `-o -`, youtube-dl still uses `-f best` format selection in order to start content delivery immediately to your player and not to wait until `bestvideo` and `bestaudio` are downloaded and muxed.

If you want to preserve the old format selection behavior (prior to youtube-dl 2015.04.26), i.e. you want to download the best available quality media served as a single file, you should explicitly specify your choice with `-f best`. You may want to add it to the [configuration file](#configuration) in order not to type it every time you run youtube-dl.

#### Format selection examples

Note that on Windows you may need to use double quotes instead of single.

```bash
# Download best mp4 format available or any other best if no mp4 available
$ youtube-dl -f 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

# Download best format available but no better than 480p
$ youtube-dl -f 'bestvideo[height<=480]+bestaudio/best[height<=480]'

# Download best video only format but no bigger than 50 MB
$ youtube-dl -f 'best[filesize<50M]'

# Download best format available via direct link over HTTP/HTTPS protocol
$ youtube-dl -f '(bestvideo+bestaudio/best)[protocol^=http]'

# Download the best video format and the best audio format without merging them
$ youtube-dl -f 'bestvideo,bestaudio' -o '%(title)s.f%(format_id)s.%(ext)s'
```
Note that in the last example, an output template is recommended as bestvideo and bestaudio may have the same file name.


# VIDEO SELECTION

Videos can be filtered by their upload date using the options `--date`, `--datebefore` or `--dateafter`. They accept dates in two formats:

 - Absolute dates: Dates in the format `YYYYMMDD`.
 - Relative dates: Dates in the format `(now|today)[+-][0-9](day|week|month|year)(s)?`

Examples:

```bash
# Download only the videos uploaded in the last 6 months
$ youtube-dl --dateafter now-6months

# Download only the videos uploaded on January 1, 1970
$ youtube-dl --date 19700101

$ # Download only the videos uploaded in the 200x decade
$ youtube-dl --dateafter 20000101 --datebefore 20091231
```

# FAQ

### I'm getting an error `Unable to extract OpenGraph title` on YouTube playlists

YouTube changed their playlist format in March 2014 and later on, so you'll need at least youtube-dl 2014.07.25 to download all YouTube videos.

If you have installed youtube-dl with a package manager, pip, setup.py or a tarball, please use that to update. Note that Ubuntu packages do not seem to get updated anymore. Since we are not affiliated with Ubuntu, there is little we can do. Feel free to [report bugs](https://bugs.launchpad.net/ubuntu/+source/youtube-dl/+filebug) to the [Ubuntu packaging people](mailto:ubuntu-motu@lists.ubuntu.com?subject=outdated%20version%20of%20youtube-dl) - all they have to do is update the package to a somewhat recent version. See above for a way to update.

### I'm getting an error when trying to use output template: `error: using output template conflicts with using title, video ID or auto number`

Make sure you are not using `-o` with any of these options `-t`, `--title`, `--id`, `-A` or `--auto-number` set in command line or in a configuration file. Remove the latter if any.

### Do I always have to pass `-citw`?

By default, youtube-dl intends to have the best options (incidentally, if you have a convincing case that these should be different, [please file an issue where you explain that](https://yt-dl.org/bug)). Therefore, it is unnecessary and sometimes harmful to copy long option strings from webpages. In particular, the only option out of `-citw` that is regularly useful is `-i`.

### I get HTTP error 402 when trying to download a video. What's this?

Apparently YouTube requires you to pass a CAPTCHA test if you download too much. We're [considering to provide a way to let you solve the CAPTCHA](https://github.com/ytdl-org/youtube-dl/issues/154), but at the moment, your best course of action is pointing a web browser to the youtube URL, solving the CAPTCHA, and restart youtube-dl.

### Do I need any other programs?

youtube-dl works fine on its own on most sites. However, if you want to convert video/audio, you'll need [avconv](https://libav.org/) or [ffmpeg](https://www.ffmpeg.org/). On some sites - most notably YouTube - videos can be retrieved in a higher quality format without sound. youtube-dl will detect whether avconv/ffmpeg is present and automatically pick the best option.

Videos or video formats streamed via RTMP protocol can only be downloaded when [rtmpdump](https://rtmpdump.mplayerhq.hu/) is installed. Downloading MMS and RTSP videos requires either [mplayer](https://mplayerhq.hu/) or [mpv](https://mpv.io/) to be installed.

### I have downloaded a video but how can I play it?

Once the video is fully downloaded, use any video player, such as [mpv](https://mpv.io/), [vlc](https://www.videolan.org/) or [mplayer](https://www.mplayerhq.hu/).

### I extracted a video URL with `-g`, but it does not play on another machine / in my web browser.

It depends a lot on the service. In many cases, requests for the video (to download/play it) must come from the same IP address and with the same cookies and/or HTTP headers. Use the `--cookies` option to write the required cookies into a file, and advise your downloader to read cookies from that file. Some sites also require a common user agent to be used, use `--dump-user-agent` to see the one in use by youtube-dl. You can also get necessary cookies and HTTP headers from JSON output obtained with `--dump-json`.

It may be beneficial to use IPv6; in some cases, the restrictions are only applied to IPv4. Some services (sometimes only for a subset of videos) do not restrict the video URL by IP address, cookie, or user-agent, but these are the exception rather than the rule.

Please bear in mind that some URL protocols are **not** supported by browsers out of the box, including RTMP. If you are using `-g`, your own downloader must support these as well.

If you want to play the video on a machine that is not running youtube-dl, you can relay the video content from the machine that runs youtube-dl. You can use `-o -` to let youtube-dl stream a video to stdout, or simply allow the player to download the files written by youtube-dl in turn.

### ERROR: no fmt_url_map or conn information found in video info

YouTube has switched to a new video info format in July 2011 which is not supported by old versions of youtube-dl. See [above](#how-do-i-update-youtube-dl) for how to update youtube-dl.

### ERROR: unable to download video

YouTube requires an additional signature since September 2012 which is not supported by old versions of youtube-dl. See [above](#how-do-i-update-youtube-dl) for how to update youtube-dl.

### Video URL contains an ampersand and I'm getting some strange output `[1] 2839` or `'v' is not recognized as an internal or external command`

That's actually the output from your shell. Since ampersand is one of the special shell characters it's interpreted by the shell preventing you from passing the whole URL to youtube-dl. To disable your shell from interpreting the ampersands (or any other special characters) you have to either put the whole URL in quotes or escape them with a backslash (which approach will work depends on your shell).

For example if your URL is https://www.youtube.com/watch?t=4&v=BaW_jenozKc you should end up with following command:

```youtube-dl 'https://www.youtube.com/watch?t=4&v=BaW_jenozKc'```

or

```youtube-dl https://www.youtube.com/watch?t=4\&v=BaW_jenozKc```

For Windows you have to use the double quotes:

```youtube-dl "https://www.youtube.com/watch?t=4&v=BaW_jenozKc"```

### ExtractorError: Could not find JS function u'OF'

In February 2015, the new YouTube player contained a character sequence in a string that was misinterpreted by old versions of youtube-dl. See [above](#how-do-i-update-youtube-dl) for how to update youtube-dl.

### HTTP Error 429: Too Many Requests or 402: Payment Required

These two error codes indicate that the service is blocking your IP address because of overuse. Usually this is a soft block meaning that you can gain access again after solving CAPTCHA. Just open a browser and solve a CAPTCHA the service suggests you and after that [pass cookies](#how-do-i-pass-cookies-to-youtube-dl) to youtube-dl. Note that if your machine has multiple external IPs then you should also pass exactly the same IP you've used for solving CAPTCHA with [`--source-address`](#network-options). Also you may need to pass a `User-Agent` HTTP header of your browser with [`--user-agent`](#workarounds).

If this is not the case (no CAPTCHA suggested to solve by the service) then you can contact the service and ask them to unblock your IP address, or - if you have acquired a whitelisted IP address already - use the [`--proxy` or `--source-address` options](#network-options) to select another IP address.

### How do I put downloads into a specific folder?

Use the `-o` to specify an [output template](#output-template), for example `-o "/home/user/videos/%(title)s-%(id)s.%(ext)s"`. If you want this for all of your downloads, put the option into your [configuration file](#configuration).

### How do I download a video starting with a `-`?

Either prepend `https://www.youtube.com/watch?v=` or separate the ID from the options with `--`:

    youtube-dl -- -wNyEUrxzFU
    youtube-dl "https://www.youtube.com/watch?v=-wNyEUrxzFU"

### How do I pass cookies to youtube-dl?

Use the `--cookies` option, for example `--cookies /path/to/cookies/file.txt`.

In order to extract cookies from browser use any conforming browser extension for exporting cookies. For example, [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) (for Chrome) or [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) (for Firefox).

Note that the cookies file must be in Mozilla/Netscape format and the first line of the cookies file must be either `# HTTP Cookie File` or `# Netscape HTTP Cookie File`. Make sure you have correct [newline format](https://en.wikipedia.org/wiki/Newline) in the cookies file and convert newlines if necessary to correspond with your OS, namely `CRLF` (`\r\n`) for Windows and `LF` (`\n`) for Unix and Unix-like systems (Linux, macOS, etc.). `HTTP Error 400: Bad Request` when using `--cookies` is a good sign of invalid newline format.

Passing cookies to youtube-dl is a good way to workaround login when a particular extractor does not implement it explicitly. Another use case is working around [CAPTCHA](https://en.wikipedia.org/wiki/CAPTCHA) some websites require you to solve in particular cases in order to get access (e.g. YouTube, CloudFlare).

### How do I stream directly to media player?

You will first need to tell youtube-dl to stream media to stdout with `-o -`, and also tell your media player to read from stdin (it must be capable of this for streaming) and then pipe former to latter. For example, streaming to [vlc](https://www.videolan.org/) can be achieved with:

    youtube-dl -o - "https://www.youtube.com/watch?v=BaW_jenozKcj" | vlc -

### How do I download only new videos from a playlist?

Use download-archive feature. With this feature you should initially download the complete playlist with `--download-archive /path/to/download/archive/file.txt` that will record identifiers of all the videos in a special file. Each subsequent run with the same `--download-archive` will download only new videos and skip all videos that have been downloaded before. Note that only successful downloads are recorded in the file.

For example, at first,

    youtube-dl --download-archive archive.txt "https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re"

will download the complete `PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re` playlist and create a file `archive.txt`. Each subsequent run will only download new videos if any:

    youtube-dl --download-archive archive.txt "https://www.youtube.com/playlist?list=PLwiyx1dc3P2JR9N8gQaQN_BCvlSlap7re"

### Should I add `--hls-prefer-native` into my config?

When youtube-dl detects an HLS video, it can download it either with the built-in downloader or ffmpeg. Since many HLS streams are slightly invalid and ffmpeg/youtube-dl each handle some invalid cases better than the other, there is an option to switch the downloader if needed.

When youtube-dl knows that one particular downloader works better for a given website, that downloader will be picked. Otherwise, youtube-dl will pick the best downloader for general compatibility, which at the moment happens to be ffmpeg. This choice may change in future versions of youtube-dl, with improvements of the built-in downloader and/or ffmpeg.

If you put either `--hls-prefer-native` or `--hls-prefer-ffmpeg` into your configuration, a different subset of videos will fail to download correctly.

