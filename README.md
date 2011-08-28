# youtube-dl

## USAGE
youtube-dl [OPTIONS] URL

## DESCRIPTION
**youtube-dl** is a small command-line program to download videos from
YouTube.com and a few more sites. It requires the Python interpreter, version
2.x (x being at least 5), and it is not platform specific. It should work in
your Unix box, in Windows or in Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.

## OPTIONS
    -h, --help               print this help text and exit
    -v, --version            print program version and exit
    -U, --update             update this program to latest stable version
    -i, --ignore-errors      continue on download errors
    -r, --rate-limit LIMIT   download rate limit (e.g. 50k or 44.6m)
    -R, --retries RETRIES    number of retries (default is 10)
    --playlist-start NUMBER  playlist video to start at (default is 1)
    --playlist-end NUMBER    playlist video to end at (default is last)
    --dump-user-agent        display the current browser identification

### Filesystem Options:
    -t, --title              use title in file name
    -l, --literal            use literal title in file name
    -A, --auto-number        number downloaded files starting from 00000
    -o, --output TEMPLATE    output filename template
    -a, --batch-file FILE    file containing URLs to download ('-' for stdin)
    -w, --no-overwrites      do not overwrite files
    -c, --continue           resume partially downloaded files
    --cookies FILE           file to dump cookie jar to
    --no-part                do not use .part files
    --no-mtime               do not use the Last-modified header to set the file
                             modification time
    --write-description      write video description to a .description file
    --write-info-json        write video metadata to a .info.json file

### Verbosity / Simulation Options:
    -q, --quiet              activates quiet mode
    -s, --simulate           do not download video
    -g, --get-url            simulate, quiet but print URL
    -e, --get-title          simulate, quiet but print title
    --get-thumbnail          simulate, quiet but print thumbnail URL
    --get-description        simulate, quiet but print video description
    --get-filename           simulate, quiet but print output filename
    --no-progress            do not print progress bar
    --console-title          display progress in console titlebar

### Video Format Options:
    -f, --format FORMAT      video format code
    --all-formats            download all available video formats
    --max-quality FORMAT     highest quality format to download

### Authentication Options:
    -u, --username USERNAME  account username
    -p, --password PASSWORD  account password
    -n, --netrc              use .netrc authentication data

### Post-processing Options:
    --extract-audio          convert video files to audio-only files (requires
                             ffmpeg and ffprobe)
    --audio-format FORMAT    "best", "aac" or "mp3"; best by default

## COPYRIGHT
**youtube-dl**: Copyright © 2006-2011 Ricardo Garcia Gonzalez. The program is
released into the public domain by the copyright holder. This README file was
originally written by Daniel Bolton (<https://github.com/dbbolton>) and is
likewise released into the public domain.

## BUGS
Bugs should be reported at: <https://github.com/phihag/youtube-dl/issues>
