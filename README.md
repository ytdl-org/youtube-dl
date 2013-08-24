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
    -h, --help                 print this help text and exit
    --version                  print program version and exit
    -U, --update               update this program to latest version. Make sure
                               that you have sufficient permissions (run with
                               sudo if needed)
    -i, --ignore-errors        continue on download errors
    --dump-user-agent          display the current browser identification
    --user-agent UA            specify a custom user agent
    --referer REF              specify a custom referer, use if the video access
                               is restricted to one domain
    --list-extractors          List all supported extractors and the URLs they
                               would handle
    --extractor-descriptions   Output descriptions of all supported extractors
    --proxy URL                Use the specified HTTP/HTTPS proxy
    --no-check-certificate     Suppress HTTPS certificate validation.

## Video Selection:
    --playlist-start NUMBER    playlist video to start at (default is 1)
    --playlist-end NUMBER      playlist video to end at (default is last)
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

## Download Options:
    -r, --rate-limit LIMIT     maximum download rate (e.g. 50k or 44.6m)
    -R, --retries RETRIES      number of retries (default is 10)
    --buffer-size SIZE         size of download buffer (e.g. 1024 or 16k)
                               (default is 1024)
    --no-resize-buffer         do not automatically adjust the buffer size. By
                               default, the buffer size is automatically resized
                               from an initial value of SIZE.

## Filesystem Options:
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

## Verbosity / Simulation Options:
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

## Video Format Options:
    -f, --format FORMAT        video format code, specifiy the order of
                               preference using slashes: "-f 22/17/18"
    --all-formats              download all available video formats
    --prefer-free-formats      prefer free video formats unless a specific one
                               is requested
    --max-quality FORMAT       highest quality format to download
    -F, --list-formats         list all available formats (currently youtube
                               only)

## Subtitle Options:
    --write-sub                write subtitle file (currently youtube only)
    --write-auto-sub           write automatic subtitle file (currently youtube
                               only)
    --only-sub                 [deprecated] alias of --skip-download
    --all-subs                 downloads all the available subtitles of the
                               video
    --list-subs                lists all available subtitles for the video
    --sub-format FORMAT        subtitle format (default=srt) ([sbv/vtt] youtube
                               only)
    --sub-lang LANGS           languages of the subtitles to download (optional)
                               separated by commas, use IETF language tags like
                               'en,pt'

## Authentication Options:
    -u, --username USERNAME    account username
    -p, --password PASSWORD    account password
    -n, --netrc                use .netrc authentication data
    --video-password PASSWORD  video password (vimeo only)

## Post-processing Options:
    -x, --extract-audio        convert video files to audio-only files (requires
                               ffmpeg or avconv and ffprobe or avprobe)
    --audio-format FORMAT      "best", "aac", "vorbis", "mp3", "m4a", "opus", or
                               "wav"; best by default
    --audio-quality QUALITY    ffmpeg/avconv audio quality specification, insert
                               a value between 0 (better) and 9 (worse) for VBR
                               or a specific bitrate like 128K (default 5)
    --recode-video FORMAT      Encode the video to another format if necessary
                               (currently supported: mp4|flv|ogg|webm)
    -k, --keep-video           keeps the video file on disk after the post-
                               processing; the video is erased by default
    --no-post-overwrites       do not overwrite post-processed files; the post-
                               processed files are overwritten by default
    --embed-subs               embed subtitles in the video (only for mp4
                               videos)

# CONFIGURATION

You can configure youtube-dl by placing default arguments (such as `--extract-audio --no-mtime` to always extract the audio and not copy the mtime) into `/etc/youtube-dl.conf` and/or `~/.config/youtube-dl.conf`.

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

	$ youtube-dl --dateafter now-6months #will only download the videos uploaded in the last 6 months
	$ youtube-dl --date 19700101 #will only download the videos uploaded in January 1, 1970
	$ youtube-dl --dateafter 20000101 --datebefore 20100101 #will only download the videos uploaded between 2000 and 2010

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

# COPYRIGHT

youtube-dl is released into the public domain by the copyright holders.

This README file was originally written by Daniel Bolton (<https://github.com/dbbolton>) and is likewise released into the public domain.

# BUGS

Bugs and suggestions should be reported at: <https://github.com/rg3/youtube-dl/issues>

Please include:

* Your exact command line, like `youtube-dl -t "http://www.youtube.com/watch?v=uHlDtZ6Oc3s&feature=channel_video_title"`. A common mistake is not to escape the `&`. Putting URLs in quotes should solve this problem.
* If possible re-run the command with `--verbose`, and include the full output, it is really helpful to us.
* The output of `youtube-dl --version`
* The output of `python --version`
* The name and version of your Operating System ("Ubuntu 11.04 x64" or "Windows 7 x64" is usually enough).

For discussions, join us in the irc channel #youtube-dl on freenode.
