# youtube-dl

Allows you to download and transcode video from supported sites. Needs ffmpeg for transcoding to work.

## Supported sites
  
  * Youtube
  * Metacafe
  * Dailymotion
  * Google
  * Photobucket
  * Yahoo
  * DepositFiles
  * Facebook
  * Sites with JW Player

## Installation

    $ sudo apt-get install ffmpeg # for Ubuntu
    $ sudo wget --no-check-certificate https://github.com/dz0ny/youtube-dl/raw/master/youtube-dl -O /usr/local/bin/youtube-dl && sudo chmod a+x /usr/local/bin/youtube-dl

## Usage
    $ youtube-dl [options] url...

    Options:
      -h, --help            print this help text and exit
      -v, --version         print program version and exit
      -U, --update          update this program to latest stable version
      -i, --ignore-errors   continue on download errors
      -r LIMIT, --rate-limit=LIMIT
                            download rate limit (e.g. 50k or 44.6m)
      -R RETRIES, --retries=RETRIES
                            number of retries (default is 10)
      --playlist-start=NUMBER
                            playlist video to start at (default is 1)
      --playlist-end=NUMBER
                            playlist video to end at (default is last)
      --dump-user-agent     display the current browser identification

      Authentication Options:
        -u USERNAME, --username=USERNAME
                            account username
        -p PASSWORD, --password=PASSWORD
                            account password
        -n, --netrc         use .netrc authentication data

      Video Format Options:
        -f FORMAT, --format=FORMAT
                            video format code
        --all-formats       download all available video formats
        --max-quality=FORMAT
                            highest quality format to download

      Verbosity / Simulation Options:
        -q, --quiet         activates quiet mode
        -s, --simulate      do not download video
        -g, --get-url       simulate, quiet but print URL
        -e, --get-title     simulate, quiet but print title
        --get-thumbnail     simulate, quiet but print thumbnail URL
        --get-description   simulate, quiet but print video description
        --get-filename      simulate, quiet but print output filename
        --no-progress       do not print progress bar
        --console-title     display progress in console titlebar

      Filesystem Options:
        -t, --title         use title in file name
        -l, --literal       use literal title in file name
        -A, --auto-number   number downloaded files starting from 00000
        -o TEMPLATE, --output=TEMPLATE
                            output filename template
        -a FILE, --batch-file=FILE
                            file containing URLs to download ('-' for stdin)
        -w, --no-overwrites
                            do not overwrite files
        -c, --continue      resume partially downloaded files
        --cookies=FILE      file to dump cookie jar to
        --no-part           do not use .part files
        --no-mtime          do not use the Last-modified header to set the file
                            modification time

      Transcoding Options (uses ffmpeg):
        -T FILE_TYPE, --transcode_to=FILE_TYPE
                            transcode to specific video or audio format (example:
                            mp3 mp4 mov mkv)
        --transcode_extra=ARGS
                            pass additional parameters to ffmpeg (example: -vcodec
                            libx264 -vpre slow -vpre ipod640 -b 2048k -acodec
                            libfaac -ab 96k)

# License 
  
  Public domain code

# Authors
  
  * Ricardo Garcia Gonzalez
  * Danny Colligan
  * Benjamin Johnson
  * Vasyl' Vavrychuk
  * Witold Baryluk
  * Paweł Paprota
  * Gergely Imreh
  * Janez Troha
