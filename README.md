# youtube-dl

## USAGE
youtube-dl [options] url [url...]

## DESCRIPTION
**youtube-dl** is a small command-line program to download videos from
YouTube.com and a few more sites. It requires the Python interpreter, version
2.x (x being at least 5), and it is not platform specific. It should work in
your Unix box, in Windows or in Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.

## OPTIONS
    -h, --help               print this help text and exit
    -v, --version            print program version and exit
    -U, --update             update this program to latest version
    -i, --ignore-errors      continue on download errors
    -r, --rate-limit LIMIT   download rate limit (e.g. 50k or 44.6m)
    -R, --retries RETRIES    number of retries (default is 10)
    --dump-user-agent        display the current browser identification
    --list-extractors        List all supported extractors and the URLs they
                             would handle

### Video Selection:
    --playlist-start NUMBER  playlist video to start at (default is 1)
    --playlist-end NUMBER    playlist video to end at (default is last)
    --match-title REGEX      download only matching titles (regex or caseless
                             sub-string)
    --reject-title REGEX     skip download for matching titles (regex or
                             caseless sub-string)
    --max-downloads NUMBER   Abort after downloading NUMBER files

### Filesystem Options:
    -t, --title              use title in file name
    -l, --literal            use literal title in file name
    -A, --auto-number        number downloaded files starting from 00000
    -o, --output TEMPLATE    output filename template. Use %(stitle)s to get the
                             title, %(uploader)s for the uploader name,
                             %(autonumber)s to get an automatically incremented
                             number, %(ext)s for the filename extension,
                             %(upload_date)s for the upload date (YYYYMMDD), and
                             %% for a literal percent
    -a, --batch-file FILE    file containing URLs to download ('-' for stdin)
    -w, --no-overwrites      do not overwrite files
    -c, --continue           resume partially downloaded files
    --no-continue            do not resume partially downloaded files (restart
                             from beginning)
    --cookies FILE           file to read cookies from and dump cookie jar in
    --no-part                do not use .part files
    --no-mtime               do not use the Last-modified header to set the file
                             modification time
    --write-description      write video description to a .description file
    --write-info-json        write video metadata to a .info.json file

### Verbosity / Simulation Options:
    -q, --quiet              activates quiet mode
    -s, --simulate           do not download the video and do not write anything
                             to disk
    --skip-download          do not download the video
    -g, --get-url            simulate, quiet but print URL
    -e, --get-title          simulate, quiet but print title
    --get-thumbnail          simulate, quiet but print thumbnail URL
    --get-description        simulate, quiet but print video description
    --get-filename           simulate, quiet but print output filename
    --get-format             simulate, quiet but print output format
    --no-progress            do not print progress bar
    --console-title          display progress in console titlebar

### Video Format Options:
    -f, --format FORMAT      video format code
    --all-formats            download all available video formats
    --max-quality FORMAT     highest quality format to download
    -F, --list-formats       list all available formats (currently youtube only)

### Authentication Options:
    -u, --username USERNAME  account username
    -p, --password PASSWORD  account password
    -n, --netrc              use .netrc authentication data

### Post-processing Options:
    --extract-audio          convert video files to audio-only files (requires
                             ffmpeg and ffprobe)
    --audio-format FORMAT    "best", "aac", "vorbis" or "mp3"; best by default
    --audio-quality QUALITY  ffmpeg audio bitrate specification, 128k by default
    -k, --keep-video         keeps the video file on disk after the post-
                             processing; the video is erased by default

## FAQ

### Can you please put the -b option back?

Most people asking this question are not aware that youtube-dl now defaults to downloading the highest available quality as reported by YouTube, which will be 1080p or 720p in some cases, so you no longer need the -b option. For some specific videos, maybe YouTube does not report them to be available in a specific high quality format you''re interested in. In that case, simply request it with the -f option and youtube-dl will try to download it.

### I get HTTP error 402 when trying to download a video. What's this?

Apparently YouTube requires you to pass a CAPTCHA test if you download too much. We''re [considering to provide a way to let you solve the CAPTCHA](https://github.com/rg3/youtube-dl/issues/154), but at the moment, your best course of action is pointing a webbrowser to the youtube URL, solving the CAPTCHA, and restart youtube-dl.

### I have downloaded a video but how can I play it?

Once the video is fully downloaded, use any video player, such as [vlc](http://www.videolan.org) or [mplayer](http://www.mplayerhq.hu/).

### The links provided by youtube-dl -g are not working anymore

The URLs youtube-dl outputs require the downloader to have the correct cookies. Use the `--cookies` option to write the required cookies into a file, and advise your downloader to read cookies from that file.

### ERROR: no fmt_url_map or conn information found in video info

youtube has switched to a new video info format in July 2011 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

## COPYRIGHT

youtube-dl is released into the public domain by the copyright holders.

This README file was originally written by Daniel Bolton (<https://github.com/dbbolton>) and is likewise released into the public domain.

## BUGS

Bugs and suggestions should be reported at: <https://github.com/rg3/youtube-dl/issues>

Please include:

* Your exact command line, like `youtube-dl -t "http://www.youtube.com/watch?v=uHlDtZ6Oc3s&feature=channel_video_title"`. A common mistake is not to escape the `&`. Putting URLs in quotes should solve this problem.
* The output of `youtube-dl --version`
* The output of `python --version`
* The name and version of your Operating System ("Ubuntu 11.04 x64" or "Windows 7 x64" is usually enough).
