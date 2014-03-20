% YOUTUBE-DL(1)

# NAME
youtube-dl - download videos from youtube.com or other video platforms

# SYNOPSIS
**youtube-dl** [OPTIONS] URL [URL...]

# DESCRIPTION
**youtube-dl** is a small command-line program to download videos from
YouTube.com and a few more sites. It requires the Python interpreter, version
2.6, 2.7, or 3.3+, and it is not platform specific. It should work on
your Unix box, on Windows or on Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.

# OPTIONS
    -h, --help                       print this help text and exit
    --version                        print program version and exit
    -U, --update                     update this program to latest version. Make
                                     sure that you have sufficient permissions
                                     (run with sudo if needed)
    -i, --ignore-errors              continue on download errors, for example to
                                     skip unavailable videos in a playlist
    --abort-on-error                 Abort downloading of further videos (in the
                                     playlist or the command line) if an error
                                     occurs
    --dump-user-agent                display the current browser identification
    --user-agent UA                  specify a custom user agent
    --referer REF                    specify a custom referer, use if the video
                                     access is restricted to one domain
    --list-extractors                List all supported extractors and the URLs
                                     they would handle
    --extractor-descriptions         Output descriptions of all supported
                                     extractors
    --proxy URL                      Use the specified HTTP/HTTPS proxy. Pass in
                                     an empty string (--proxy "") for direct
                                     connection
    --no-check-certificate           Suppress HTTPS certificate validation.
    --prefer-insecure                Use an unencrypted connection to retrieve
                                     information about the video. (Currently
                                     supported only for YouTube)
    --cache-dir DIR                  Location in the filesystem where youtube-dl
                                     can store some downloaded information
                                     permanently. By default $XDG_CACHE_HOME
                                     /youtube-dl or ~/.cache/youtube-dl . At the
                                     moment, only YouTube player files (for
                                     videos with obfuscated signatures) are
                                     cached, but that may change.
    --no-cache-dir                   Disable filesystem caching
    --socket-timeout None            Time to wait before giving up, in seconds
    --bidi-workaround                Work around terminals that lack
                                     bidirectional text support. Requires bidiv
                                     or fribidi executable in PATH
    --default-search PREFIX          Use this prefix for unqualified URLs. For
                                     example "gvsearch2:" downloads two videos
                                     from google videos for  youtube-dl "large
                                     apple". By default (with value "auto")
                                     youtube-dl guesses.
    --ignore-config                  Do not read configuration files. When given
                                     in the global configuration file /etc
                                     /youtube-dl.conf: do not read the user
                                     configuration in ~/.config/youtube-dl.conf
                                     (%APPDATA%/youtube-dl/config.txt on
                                     Windows)

## Video Selection:
    --playlist-start NUMBER          playlist video to start at (default is 1)
    --playlist-end NUMBER            playlist video to end at (default is last)
    --match-title REGEX              download only matching titles (regex or
                                     caseless sub-string)
    --reject-title REGEX             skip download for matching titles (regex or
                                     caseless sub-string)
    --max-downloads NUMBER           Abort after downloading NUMBER files
    --min-filesize SIZE              Do not download any videos smaller than
                                     SIZE (e.g. 50k or 44.6m)
    --max-filesize SIZE              Do not download any videos larger than SIZE
                                     (e.g. 50k or 44.6m)
    --date DATE                      download only videos uploaded in this date
    --datebefore DATE                download only videos uploaded on or before
                                     this date (i.e. inclusive)
    --dateafter DATE                 download only videos uploaded on or after
                                     this date (i.e. inclusive)
    --min-views COUNT                Do not download any videos with less than
                                     COUNT views
    --max-views COUNT                Do not download any videos with more than
                                     COUNT views
    --no-playlist                    download only the currently playing video
    --age-limit YEARS                download only videos suitable for the given
                                     age
    --download-archive FILE          Download only videos not listed in the
                                     archive file. Record the IDs of all
                                     downloaded videos in it.
    --include-ads                    Download advertisements as well
                                     (experimental)
    --youtube-include-dash-manifest  Try to download the DASH manifest on
                                     YouTube videos (experimental)

## Download Options:
    -r, --rate-limit LIMIT           maximum download rate in bytes per second
                                     (e.g. 50K or 4.2M)
    -R, --retries RETRIES            number of retries (default is 10)
    --buffer-size SIZE               size of download buffer (e.g. 1024 or 16K)
                                     (default is 1024)
    --no-resize-buffer               do not automatically adjust the buffer
                                     size. By default, the buffer size is
                                     automatically resized from an initial value
                                     of SIZE.

## Filesystem Options:
    -t, --title                      use title in file name (default)
    --id                             use only video ID in file name
    -l, --literal                    [deprecated] alias of --title
    -A, --auto-number                number downloaded files starting from 00000
    -o, --output TEMPLATE            output filename template. Use %(title)s to
                                     get the title, %(uploader)s for the
                                     uploader name, %(uploader_id)s for the
                                     uploader nickname if different,
                                     %(autonumber)s to get an automatically
                                     incremented number, %(ext)s for the
                                     filename extension, %(format)s for the
                                     format description (like "22 - 1280x720" or
                                     "HD"), %(format_id)s for the unique id of
                                     the format (like Youtube's itags: "137"),
                                     %(upload_date)s for the upload date
                                     (YYYYMMDD), %(extractor)s for the provider
                                     (youtube, metacafe, etc), %(id)s for the
                                     video id, %(playlist)s for the playlist the
                                     video is in, %(playlist_index)s for the
                                     position in the playlist and %% for a
                                     literal percent. %(height)s and %(width)s
                                     for the width and height of the video
                                     format. %(resolution)s for a textual
                                     description of the resolution of the video
                                     format. Use - to output to stdout. Can also
                                     be used to download to a different
                                     directory, for example with -o '/my/downloa
                                     ds/%(uploader)s/%(title)s-%(id)s.%(ext)s' .
    --autonumber-size NUMBER         Specifies the number of digits in
                                     %(autonumber)s when it is present in output
                                     filename template or --auto-number option
                                     is given
    --restrict-filenames             Restrict filenames to only ASCII
                                     characters, and avoid "&" and spaces in
                                     filenames
    -a, --batch-file FILE            file containing URLs to download ('-' for
                                     stdin)
    --load-info FILE                 json file containing the video information
                                     (created with the "--write-json" option)
    -w, --no-overwrites              do not overwrite files
    -c, --continue                   force resume of partially downloaded files.
                                     By default, youtube-dl will resume
                                     downloads if possible.
    --no-continue                    do not resume partially downloaded files
                                     (restart from beginning)
    --cookies FILE                   file to read cookies from and dump cookie
                                     jar in
    --no-part                        do not use .part files
    --no-mtime                       do not use the Last-modified header to set
                                     the file modification time
    --write-description              write video description to a .description
                                     file
    --write-info-json                write video metadata to a .info.json file
    --write-annotations              write video annotations to a .annotation
                                     file
    --write-thumbnail                write thumbnail image to disk

## Verbosity / Simulation Options:
    -q, --quiet                      activates quiet mode
    -s, --simulate                   do not download the video and do not write
                                     anything to disk
    --skip-download                  do not download the video
    -g, --get-url                    simulate, quiet but print URL
    -e, --get-title                  simulate, quiet but print title
    --get-id                         simulate, quiet but print id
    --get-thumbnail                  simulate, quiet but print thumbnail URL
    --get-description                simulate, quiet but print video description
    --get-duration                   simulate, quiet but print video length
    --get-filename                   simulate, quiet but print output filename
    --get-format                     simulate, quiet but print output format
    -j, --dump-json                  simulate, quiet but print JSON information
    --newline                        output progress bar as new lines
    --no-progress                    do not print progress bar
    --console-title                  display progress in console titlebar
    -v, --verbose                    print various debugging information
    --dump-intermediate-pages        print downloaded pages to debug problems
                                     (very verbose)
    --write-pages                    Write downloaded intermediary pages to
                                     files in the current directory to debug
                                     problems
    --print-traffic                  Display sent and read HTTP traffic

## Video Format Options:
    -f, --format FORMAT              video format code, specify the order of
                                     preference using slashes: "-f 22/17/18".
                                     "-f mp4" and "-f flv" are also supported.
                                     You can also use the special names "best",
                                     "bestvideo", "bestaudio", "worst",
                                     "worstvideo" and "worstaudio". By default,
                                     youtube-dl will pick the best quality.
    --all-formats                    download all available video formats
    --prefer-free-formats            prefer free video formats unless a specific
                                     one is requested
    --max-quality FORMAT             highest quality format to download
    -F, --list-formats               list all available formats

## Subtitle Options:
    --write-sub                      write subtitle file
    --write-auto-sub                 write automatic subtitle file (youtube
                                     only)
    --all-subs                       downloads all the available subtitles of
                                     the video
    --list-subs                      lists all available subtitles for the video
    --sub-format FORMAT              subtitle format (default=srt) ([sbv/vtt]
                                     youtube only)
    --sub-lang LANGS                 languages of the subtitles to download
                                     (optional) separated by commas, use IETF
                                     language tags like 'en,pt'

## Authentication Options:
    -u, --username USERNAME          account username
    -p, --password PASSWORD          account password
    -n, --netrc                      use .netrc authentication data
    --video-password PASSWORD        video password (vimeo, smotri)

## Post-processing Options:
    -x, --extract-audio              convert video files to audio-only files
                                     (requires ffmpeg or avconv and ffprobe or
                                     avprobe)
    --audio-format FORMAT            "best", "aac", "vorbis", "mp3", "m4a",
                                     "opus", or "wav"; best by default
    --audio-quality QUALITY          ffmpeg/avconv audio quality specification,
                                     insert a value between 0 (better) and 9
                                     (worse) for VBR or a specific bitrate like
                                     128K (default 5)
    --recode-video FORMAT            Encode the video to another format if
                                     necessary (currently supported:
                                     mp4|flv|ogg|webm)
    -k, --keep-video                 keeps the video file on disk after the
                                     post-processing; the video is erased by
                                     default
    --no-post-overwrites             do not overwrite post-processed files; the
                                     post-processed files are overwritten by
                                     default
    --embed-subs                     embed subtitles in the video (only for mp4
                                     videos)
    --add-metadata                   write metadata to the video file
    --xattrs                         write metadata to the video file's xattrs
                                     (using dublin core and xdg standards)
    --prefer-avconv                  Prefer avconv over ffmpeg for running the
                                     postprocessors (default)
    --prefer-ffmpeg                  Prefer ffmpeg over avconv for running the
                                     postprocessors

# CONFIGURATION

You can configure youtube-dl by placing default arguments (such as `--extract-audio --no-mtime` to always extract the audio and not copy the mtime) into `/etc/youtube-dl.conf` and/or `~/.config/youtube-dl/config`. On Windows, the configuration file locations are `%APPDATA%\youtube-dl\config.txt` and `C:\Users\<Yourname>\youtube-dl.conf`.

# OUTPUT TEMPLATE

The `-o` option allows users to indicate a template for the output file names. The basic usage is not to set any template arguments when downloading a single file, like in `youtube-dl -o funny_video.flv "http://some/video"`. However, it may contain special sequences that will be replaced when downloading each video. The special sequences have the format `%(NAME)s`. To clarify, that is a percent symbol followed by a name in parenthesis, followed by a lowercase S. Allowed names are:

 - `id`: The sequence will be replaced by the video identifier.
 - `url`: The sequence will be replaced by the video URL.
 - `uploader`: The sequence will be replaced by the nickname of the person who uploaded the video.
 - `upload_date`: The sequence will be replaced by the upload date in YYYYMMDD format.
 - `title`: The sequence will be replaced by the video title.
 - `ext`: The sequence will be replaced by the appropriate extension (like flv or mp4).
 - `epoch`: The sequence will be replaced by the Unix epoch when creating the file.
 - `autonumber`: The sequence will be replaced by a five-digit number that will be increased with each download, starting at zero.
 - `playlist`: The name or the id of the playlist that contains the video.
 - `playlist_index`: The index of the video in the playlist, a five-digit number.

The current default template is `%(title)s-%(id)s.%(ext)s`.

In some cases, you don't want special characters such as 中, spaces, or &, such as when transferring the downloaded filename to a Windows system or the filename through an 8bit-unsafe channel. In these cases, add the `--restrict-filenames` flag to get a shorter title:

    $ youtube-dl --get-filename -o "%(title)s.%(ext)s" BaW_jenozKc
    youtube-dl test video ''_ä↭𝕐.mp4    # All kinds of weird characters
    $ youtube-dl --get-filename -o "%(title)s.%(ext)s" BaW_jenozKc --restrict-filenames
    youtube-dl_test_video_.mp4          # A simple file name

# VIDEO SELECTION

Videos can be filtered by their upload date using the options `--date`, `--datebefore` or `--dateafter`, they accept dates in two formats:

 - Absolute dates: Dates in the format `YYYYMMDD`.
 - Relative dates: Dates in the format `(now|today)[+-][0-9](day|week|month|year)(s)?`
 
Examples:

    # Download only the videos uploaded in the last 6 months
    $ youtube-dl --dateafter now-6months

    # Download only the videos uploaded on January 1, 1970
    $ youtube-dl --date 19700101

    $ # will only download the videos uploaded in the 200x decade
    $ youtube-dl --dateafter 20000101 --datebefore 20091231

# FAQ

### Can you please put the -b option back?

Most people asking this question are not aware that youtube-dl now defaults to downloading the highest available quality as reported by YouTube, which will be 1080p or 720p in some cases, so you no longer need the `-b` option. For some specific videos, maybe YouTube does not report them to be available in a specific high quality format you're interested in. In that case, simply request it with the `-f` option and youtube-dl will try to download it.

### I get HTTP error 402 when trying to download a video. What's this?

Apparently YouTube requires you to pass a CAPTCHA test if you download too much. We're [considering to provide a way to let you solve the CAPTCHA](https://github.com/rg3/youtube-dl/issues/154), but at the moment, your best course of action is pointing a webbrowser to the youtube URL, solving the CAPTCHA, and restart youtube-dl.

### I have downloaded a video but how can I play it?

Once the video is fully downloaded, use any video player, such as [vlc](http://www.videolan.org) or [mplayer](http://www.mplayerhq.hu/).

### The links provided by youtube-dl -g are not working anymore

The URLs youtube-dl outputs require the downloader to have the correct cookies. Use the `--cookies` option to write the required cookies into a file, and advise your downloader to read cookies from that file. Some sites also require a common user agent to be used, use `--dump-user-agent` to see the one in use by youtube-dl.

### ERROR: no fmt_url_map or conn information found in video info

youtube has switched to a new video info format in July 2011 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

### ERROR: unable to download video ###

youtube requires an additional signature since September 2012 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

### SyntaxError: Non-ASCII character ###

The error

    File "youtube-dl", line 2
    SyntaxError: Non-ASCII character '\x93' ...

means you're using an outdated version of Python. Please update to Python 2.6 or 2.7.

### What is this binary file? Where has the code gone?

Since June 2012 (#342) youtube-dl is packed as an executable zipfile, simply unzip it (might need renaming to `youtube-dl.zip` first on some systems) or clone the git repository, as laid out above. If you modify the code, you can run it by executing the `__main__.py` file. To recompile the executable, run `make youtube-dl`.

### The exe throws a *Runtime error from Visual C++*

To run the exe you need to install first the [Microsoft Visual C++ 2008 Redistributable Package](http://www.microsoft.com/en-us/download/details.aspx?id=29).

# DEVELOPER INSTRUCTIONS

Most users do not need to build youtube-dl and can [download the builds](http://rg3.github.io/youtube-dl/download.html) or get them from their distribution.

To run youtube-dl as a developer, you don't need to build anything either. Simply execute

    python -m youtube_dl

To run the test, simply invoke your favorite test runner, or execute a test file directly; any of the following work:

    python -m unittest discover
    python test/test_download.py
    nosetests

If you want to create a build of youtube-dl yourself, you'll need

* python
* make
* pandoc
* zip
* nosetests

### Adding support for a new site

If you want to add support for a new site, copy *any* [recently modified](https://github.com/rg3/youtube-dl/commits/master/youtube_dl/extractor) file in `youtube_dl/extractor`, add an import in [`youtube_dl/extractor/__init__.py`](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/__init__.py). Have a look at [`youtube_dl/common/extractor/common.py`](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/common.py) for possible helper methods and a [detailed description of what your extractor should return](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/common.py#L38). Don't forget to run the tests with `python test/test_download.py TestDownload.test_YourExtractor`! For a detailed tutorial, refer to [this blog post](http://filippo.io/add-support-for-a-new-video-site-to-youtube-dl/).

# BUGS

Bugs and suggestions should be reported at: <https://github.com/rg3/youtube-dl/issues> . Unless you were prompted so or there is another pertinent reason (e.g. GitHub fails to accept the bug report), please do not send bug reports via personal email.

Please include the full output of the command when run with `--verbose`. The output (including the first lines) contain important debugging information. Issues without the full output are often not reproducible and therefore do not get solved in short order, if ever.

For discussions, join us in the irc channel #youtube-dl on freenode.

When you submit a request, please re-read it once to avoid a couple of mistakes (you can and should use this as a checklist):

### Is the description of the issue itself sufficient?

We often get issue reports that we cannot really decipher. While in most cases we eventually get the required information after asking back multiple times, this poses an unnecessary drain on our resources. Many contributors, including myself, are also not native speakers, so we may misread some parts.

So please elaborate on what feature you are requesting, or what bug you want to be fixed. Make sure that it's obvious

- What the problem is
- How it could be fixed
- How your proposed solution would look like

If your report is shorter than two lines, it is almost certainly missing some of these, which makes it hard for us to respond to it. We're often too polite to close the issue outright, but the missing info makes misinterpretation likely. As a commiter myself, I often get frustrated by these issues, since the only possible way for me to move forward on them is to ask for clarification over and over.

For bug reports, this means that your report should contain the *complete* output of youtube-dl when called with the -v flag. The error message you get for (most) bugs even says so, but you would not believe how many of our bug reports do not contain this information.

Site support requests must contain an example URL. An example URL is a URL you might want to download, like http://www.youtube.com/watch?v=BaW_jenozKc . There should be an obvious video present. Except under very special circumstances, the main page of a video service (e.g. http://www.youtube.com/ ) is *not* an example URL.

###  Are you using the latest version?

Before reporting any issue, type youtube-dl -U. This should report that you're up-to-date. About 20% of the reports we receive are already fixed, but people are using outdated versions. This goes for feature requests as well.

###  Is the issue already documented?

Make sure that someone has not already opened the issue you're trying to open. Search at the top of the window or at https://github.com/rg3/youtube-dl/search?type=Issues . If there is an issue, feel free to write something along the lines of "This affects me as well, with version 2015.01.01. Here is some more information on the issue: ...". While some issues may be old, a new post into them often spurs rapid activity.

###  Why are existing options not enough?

Before requesting a new feature, please have a quick peek at [the list of supported options](https://github.com/rg3/youtube-dl/blob/master/README.md#synopsis). Many feature requests are for features that actually exist already! Please, absolutely do show off your work in the issue report and detail how the existing similar options do *not* solve your problem.

###  Is there enough context in your bug report?

People want to solve problems, and often think they do us a favor by breaking down their larger problems (e.g. wanting to skip already downloaded files) to a specific request (e.g. requesting us to look whether the file exists before downloading the info page). However, what often happens is that they break down the problem into two steps: One simple, and one impossible (or extremely complicated one).

We are then presented with a very complicated request when the original problem could be solved far easier, e.g. by recording the downloaded video IDs in a separate file. To avoid this, you must include the greater context where it is non-obvious. In particular, every feature request that does not consist of adding support for a new site should contain a use case scenario that explains in what situation the missing feature would be useful.

###  Does the issue involve one problem, and one problem only?

Some of our users seem to think there is a limit of issues they can or should open. There is no limit of issues they can or should open. While it may seem appealing to be able to dump all your issues into one ticket, that means that someone who solves one of your issues cannot mark the issue as closed. Typically, reporting a bunch of issues leads to the ticket lingering since nobody wants to attack that behemoth, until someone mercifully splits the issue into multiple ones.

In particular, every site support request issue should only pertain to services at one site (generally under a common domain, but always using the same backend technology). Do not request support for vimeo user videos, Whitehouse podcasts, and Google Plus pages in the same issue. Also, make sure that you don't post bug reports alongside feature requests. As a rule of thumb, a feature request does not include outputs of youtube-dl that are not immediately related to the feature at hand. Do not post reports of a network error alongside the request for a new video service.

###  Is anyone going to need the feature?

Only post features that you (or an incapicated friend you can personally talk to) require. Do not post features because they seem like a good idea. If they are really useful, they will be requested by someone who requires them.

###  Is your question about youtube-dl?

It may sound strange, but some bug reports we receive are completely unrelated to youtube-dl and relate to a different or even the reporter's own application. Please make sure that you are actually using youtube-dl. If you are using a UI for youtube-dl, report the bug to the maintainer of the actual application providing the UI. On the other hand, if your UI for youtube-dl fails in some way you believe is related to youtube-dl, by all means, go ahead and report the bug.

# COPYRIGHT

youtube-dl is released into the public domain by the copyright holders.

This README file was originally written by Daniel Bolton (<https://github.com/dbbolton>) and is likewise released into the public domain.
