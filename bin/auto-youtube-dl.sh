#!/bin/bash

export PATH=$PATH:/usr/local/bin:/usr/local/sbin

# This is a high quality bash script to have simple files instead of multiple
# youtube-dl terminal sessions. Create the file and forget about any issues,
# they will be handled by this script.
#
# Supports Cygwin.
#
# Finely written documentation is below, here are only color definitions

# formats
_RST_='\033[0m' # resets color and format
_RVS_='\033[27m'
_BLD='\033[1m'
_DIM='\033[2m'
_UND='\033[4m'
_BlK='\033[5m'
_RVS='\033[7m'
_HID='\033[8m'
_BU='\033[1m\033[4m'

# Regular Colors
C_BLACK='\033[0;30m'
C_RED='\033[0;31m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[1;33m'
C_BLUE='\033[0;34m'
C_MAGENTA='\033[0;35m'
C_CYAN='\033[0;36m'
C_WHITE='\033[1;37m'
C_BROWN='\033[0;33m'
C_GRAY='\033[0;30m'

# High Intensty
CI_BLACK='\033[1;30m'
CI_RED='\033[1;31m'
CI_GREEN='\033[1;32m'
CI_BLUE='\033[1;34m'
CI_MAGENTA='\033[1;35m'
CI_CYAN='\033[1;36m'
CI_BROWN='\033[1;33m'
CI_GRAY='\033[1;30m'

export _RST_ _RVS_ _BLD _DIM _UND _BlK _RVS _HID _BU C_BLACK C_RED C_GREEN C_YELLOW C_BLUE C_MAGENTA C_CYAN C_WHITE C_BROWN C_GRAY CI_BLACK CI_RED CI_GREEN CI_BLUE CI_MAGENTA CI_CYAN CI_BROWN CI_GRAY


#
# The script will automatically download multiple videos from Youtube, Vimeo
# and other sites supported by youtube-dl
#
# The queue is intended to be a Dropbox subdirectory, with text files, each
# containing the URL of the video to download
#
# The download will restart many times, at least for 48 hours
# 

#
# Here is more information on available advanced functions
# - third line in the .txt file can contain youtube-dl options (e.g. -r 100k)
# - you can edit the text file (it will have *.used extension after the download starts)
#   and change the options, and auto-youtube-dl will restart the download (just saving
#   without changing the file will also cause restart); this works when there is
#   the crontab entry for this script
# - on second line, you can put BASH commands; they will be executed ahead of the
#   download (example: "sleep 120")
# - on fourth line, auto-youtube-dl will put video's title and duration
# - each download will be restarted after each 15 minutes to clean out any stalls
#   inside youtube-dl or on the network
#
#
# Example: .txt file can look like this:
#
# www.youtube.com/watch?v=Foo
# sleep 120
# -r 100k
# An example title 1:09
#
# Fourth line is the added one.
#

#
# Much below is an approach to make you change name of directories
# instead of defining paths.
#
# If you have your Dropbox (Google, etc.) directory in /usr/local/var/Dropbox
# or similar fussy location, then you will know what to do anyway (hint: change
# BPATH* to /usr/local/var)
#
# The difficulty is Windows - Unix portability. This is the cause for
# existence of BPATH and BPATH2.
#
# You should need only to define:
# - CLOUD_DIR
# - QUEUE_SUBDIR
# - VIDEO_DOWNLOAD_SUBDIR
# - optional: MOVE_AFTER_DOWNLOAD_PATH
#
# The rest will be deduced and created in your Windows/Unix user directory
#
# Check out the FORMATS variable, by default it is set to medium quality
#

# Types of variables:
# *_DIR: relative to $HOME and then to %USERPROFILE%, i.e. to $BPATH, $BPATH2
# *_SUBDIR: relative to corresponding DIR
# *_PATH: absolute path

# Base paths (unix - $HOME, windows - $USERPROFILE)
BPATH="$HOME"
BPATH2="$USERPROFILE"

CLOUD_DIR="Dropbox"                 # as ever: searched for in $BPATH, then $BPATH2
QUEUE_SUBDIR="var/youtube-dl"       # Under CLOUD_DIR. Holds the .txt with the URL to download
VIDEO_DOCUMENTS_DIR="Movies"        # As ever: $BPATH/*, then $BPATH2/*
VIDEO_DOCUMENTS_DIR2="Videos"       # (four combinations, first existing is being used)
VIDEO_DOWNLOAD_SUBDIR="youtube"     # Under $VIDEO_DOCUMENTS_DIR* (the first one found). Target download directory

# Result of having "Movies" and "Dropbox" dirs under "/home/foo" path
# /home/foo/Dropbox/var/youtube-dl  - queue directory (with the .txt files)
# /home/foo/Movies/youtube - target download directory

# Move fully downloaded file into this path
# MOVE_AFTER_DOWNLOAD_PATH="/home/foo/iTunes auto add/"

# Example crontab entry:
# * * * * * /usr/local/bin/auto-youtube-dl.sh >> /var/auto-ydl.log 2>&1

SLEEP_TIME=50
FORMATS="18/504x336/22/35/34/h264-sd/43/h264-hd/flv/vp6-sd/0/low/high"
OPTIONS=( --add-metadata --restrict-filenames --no-playlist --socket-timeout 60 --no-call-home )
TITLE_DURATION_OPTIONS=( --get-title --get-duration --no-playlist --socket-timeout 60 --no-call-home )
YDL_NAME_PATTERN='%(title)s.%(ext)s' # Used when explicit query of video's title fails

# EXAMPLE OUTPUT of file:
#
# https://www.youtube.com/watch?v=_vK84lvwQwo
# sleep 5
# -r 10k
# Atari Basic programming example 3:00
#
# :

# ./auto-youtube-dl.sh
# [pid: 57243] 2015-07-29 12:36:56 -------------------- example.txt sleep 5 -r 10k
# [pid: 57243] 2015-07-29 12:37:03 `Atari Basic programming example' [3:00s] : _vK84lvwQwo
# 
# [pid: 57243] 2015-07-29 12:37:03 STARTING download of <<example.txt>> with the command: youtube-dl -r 10k -f 18/504x336/22/35/34/h264-sd/43/h264-hd/flv/vp6-sd/0/low/high --no-progress --add-metadata --restrict-filenames --no-playlist --socket-timeout 60 --no-call-home -o /home/foo/Movies/youtube/Atari_Basic_programming_example.%(ext)s https://www.youtube.com/watch?v=_vK84lvwQwo
# [pid: 57243] 2015-07-29 12:37:03 youtube-dl PID is 57320
# [youtube] _vK84lvwQwo: Downloading webpage
# [youtube] _vK84lvwQwo: Extracting video information
# [youtube] _vK84lvwQwo: Downloading DASH manifest
# [download] Destination: /home/foo/Movies/youtube/Atari_Basic_programming_example.mp4
# 
# (now updated the file changing -r 10k to -r 200k)
#
# [pid: 57243] 2015-07-29 12:39:21 Requeueing <<example.txt>>
# [pid: 57243] 2015-07-29 12:39:21 Download of <<example.txt>> halted at attempt 1 / 3456
#
# [pid: 57243] 2015-07-29 12:39:24 Aborted <<example.txt>> : `Atari Basic programming example' [3:00s] : _vK84lvwQwo
#
# Running ./auto-youtube-dl.sh again would use the updated file, and then you would in the end see:
# 
# [download] Download completed
# [ffmpeg] Adding metadata to '/home/foo/Movies/youtube/Atari_Basic_programming_example.mp4'
# [pid: 57641] 2015-07-29 12:39:47 Download of <<example.txt>> successful (# of attempts: 1, time: 0m)
# [pid: 57641] 2015-07-29 12:39:47 Atari_Basic_programming_example.mp4 MOVED
# 
# The "MOVED" line is the result of having MOVE_AFTER_DOWNLOAD_PATH set


##
## Below is the main script's body
##


# Store PID of this script's shell
MAIN_PID=$$

#
# Helper functions
#
mydate() {
    echo "[pid: $MAIN_PID] `date '+%Y-%m-%d %H%:%M:%S'`"
}

timestamp() {
    date +"%s"
}

# Gets list of children pids
get_children_pids() {
    ps -o ppid,pid -A | egrep '^ *'$1' ' | awk '{ print $2 }'
}

# If the queue file has changed, then requeue it again
# and quit to restart the download
check_for_update() {
    [ ! -f "/tmp/ydlstart.$MAIN_PID" ] && return
    queue_file="$(</tmp/ydlstart.$MAIN_PID)"

    # Queue file updated?
    if [ "/tmp/ydlstart.$MAIN_PID" -ot "${queue_file%.txt}.used" ]; then
        # Rename the queue file back to ".txt" extension and quit
        echo -e "`mydate` ${C_YELLOW}Requeueing${_RST_} <<${CI_GREEN}`basename "$queue_file"`${_RST_}>>"

        YPID=$(echo "`cat 2>/dev/null /tmp/ydlpid.$MAIN_PID`" | sed -e 's/$/ -0/' | bc)
        [ "$YPID" -gt 100 ] && kill 2>/dev/null -15 "$YPID"

        sleep 3
        mv -f "${queue_file%.txt}.used" "$queue_file"
        kill 2>/dev/null -15 "$MAIN_PID"
    fi
}

# Repeately restart the download after some time to wipe
# out any stalls inside youtube-dl or on the network.
trim_process() {
    while (( 1 )); do
        # Wait 5 seconds 20 times, checking for update of the .txt (now .used) file
        wait_repeats=20
        while (( wait_repeats-- )); do
            check_for_update
            sleep $(( SLEEP_TIME / 10 ))
        done

        YPID=$(echo "`cat 2>/dev/null /tmp/ydlpid.$MAIN_PID`" | sed -e 's/$/ -0/' | bc)
        if [ "$YPID" -gt 100 ]; then
            # Use bc to remove leading zeros by subtracting 0, and
            # in case of empty input, to just put "0" in the result
            TIME=$(echo "`ps -o etime= -p $YPID`" | sed -e 's/[^0-9]//g' -e 's/$/ -0/' | bc)

            # Break the download if it runs for 00:15:00 or more
            [ "$TIME" -le 1500 ] && continue

            # Here are the terminating signals
            rm -f /tmp/ydlpid.$MAIN_PID
            kill 2>/dev/null -15 "$YPID" && sleep 4
            kill 2>/dev/null -9 "$YPID"
        fi
    done
}

# Stops background processes
cleanup() {
    # Stop youtube-dl if it runs
    YDL_PID=`echo $YDL_PID | sed 's/[^0-9].*/0/g'`
    (( YDL_PID = YDL_PID + 0 ))
    [ "$YDL_PID" -gt 100 ] && kill 2>/dev/null -15 "$YDL_PID"

    # Detect any other children
    for i in `get_children_pids $MAIN_PID`; do
        kill 2>/dev/null -15 "$i"
    done
    for i in `get_children_pids $MAIN_PID`; do
        LANG=C sleep 0.5
        kill 2>/dev/null -9 "$i"
    done

    # Remove temporary files
    rm -f /tmp/ydl.$MAIN_PID /tmp/ydlpid.$MAIN_PID /tmp/ydlstart.$MAIN_PID
}

# Cleans up children processes, outputs message
interrupted_exit() {
    # Inform about being aborted
    echo -e "\n`mydate` ${C_RED}Aborted${_RST_} <<${CI_GREEN}${filename}${_RST_}>> :"\
        "${C_RED}\`$vtitle'${_RST_} [${C_CYAN}${vduration}s${_RST_}] : $urlid"

    exit 100
}

trap "interrupted_exit" SIGINT SIGTERM
trap "cleanup" EXIT

#
# 1. Establish queue dir
#

if [ -d "$BPATH/$CLOUD_DIR" ]; then
    QUEUE_PATH="$BPATH/$CLOUD_DIR/$QUEUE_SUBDIR"
elif [ -d "$BPATH2/$CLOUD_DIR" ]; then
    QUEUE_PATH="$BPATH2/$CLOUD_DIR/$QUEUE_SUBDIR"
else
    echo "Error: no cloud dir '$CLOUD_DIR' found either in '$BPATH' or '$BPATH2'"
    exit 1
fi

mkdir -p "$QUEUE_PATH"

#
# 2. Establish destination download dir
#

if [ -d "$BPATH/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR" ]; then
    OUTPUT_VIDEO_PATH="$BPATH/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR"
elif [ -d "$BPATH2/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR" ]; then
    OUTPUT_VIDEO_PATH="$BPATH2/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR"
else
    if [ -d "$BPATH/$VIDEO_DOCUMENTS_DIR" ]; then
        OUTPUT_VIDEO_PATH="$BPATH/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR"
    elif [ -d "$BPATH2/$VIDEO_DOCUMENTS_DIR" ]; then
        OUTPUT_VIDEO_PATH="$BPATH2/$VIDEO_DOCUMENTS_DIR/$VIDEO_DOWNLOAD_SUBDIR"
    else
        if [ -d "$BPATH/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR" ]; then
            OUTPUT_VIDEO_PATH="$BPATH/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR"
        elif [ -d "$BPATH2/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR" ]; then
            OUTPUT_VIDEO_PATH="$BPATH2/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR"
        else
            if [ -d "$BPATH/$VIDEO_DOCUMENTS_DIR2" ]; then
                OUTPUT_VIDEO_PATH="$BPATH/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR"
            elif [ -d "$BPATH2/$VIDEO_DOCUMENTS_DIR2" ]; then
                OUTPUT_VIDEO_PATH="$BPATH2/$VIDEO_DOCUMENTS_DIR2/$VIDEO_DOWNLOAD_SUBDIR"
            else
                echo "No video dir '$VIDEO_DOCUMENTS_DIR' or '$VIDEO_DOCUMENTS_DIR2' found in '$BPATH' and '$BPATH2'"
                echo "And no download dir '$VIDEO_DOWNLOAD_SUBDIR' could be created"
                exit 1
            fi
        fi
        mkdir -p "$OUTPUT_VIDEO_PATH"
    fi
fi

if [ "$1" = "-v" ]; then
    echo "`mydate` QUEUE_PATH: $QUEUE_PATH"
    echo "`mydate` OUTPUT_VIDEO_PATH: $OUTPUT_VIDEO_PATH"
fi

# Variable to store youtube-dl PID
YDL_PID="0"

# This is minimum 48 hours of waiting for re-download
# (plus the time of actual downloading)
MAXRETRIES=$(( 48*3600 / SLEEP_TIME ))
RETRY=0
# Title isn't needed for actual download so try only a few times
TITLEMAXRETRIES=10
TITLERETRY=0

function move_finished {
    [ "$MOVE_AFTER_DOWNLOAD_PATH" = "" ] && return
    [ ! -d "$MOVE_AFTER_DOWNLOAD_PATH" ] && return
    cd $OUTPUT_VIDEO_PATH || return

    # Wait for ffmpeg to finish writing meta data
    if ls | grep -F .temp. >/dev/null 2>&1; then
        sleep 5
    fi

    {
        MVOUTPUT=`mv 2>/dev/null -vf *.mp4 *.flv *.m4a "$MOVE_AFTER_DOWNLOAD_PATH"`
    }

    if [ ! -z "$MVOUTPUT" ]; then
        echo -e "`mydate` ${C_BLUE}${MVOUTPUT}" | sed 's/->.*$/MOVED/g'
        echo -e ${_RST_}
    fi
}

move_finished

ALREADY_RUNNING=`ps -ae | grep -v grep | egrep -c '/bin/bash.*n1auto-youtube-dl.*'`
(( ALREADY_RUNNING = ALREADY_RUNNING - 1 ))
if [[ $ALREADY_RUNNING -gt 5 ]]; then
    # Are there any priority (a-...) files?
    files=`ls 2>/dev/null $QUEUE_PATH | grep 2>/dev/null '^a-[^ ]*.txt'`
    if [ -z "$files" ]; then
        echo "`mydate` Too many downloads ($ALREADY_RUNNING), exiting"
        exit
    fi
fi

if [ "$1" = "-v" ]; then
    # If no terminal (i.e. -t 1 is false) then use basic
    # progress bar that isn't animated (--newline option)
    [ -t 1 ] || OPTIONS=( --newline "${OPTIONS[@]}" )
else
    # Quiet mode
    OPTIONS=( --no-progress "${OPTIONS[@]}" )
fi

# Prepend the $FORMATS
OPTIONS=( -f "$FORMATS" "${OPTIONS[@]}" )

trim_process &

cd "$OUTPUT_VIDEO_PATH"

# Iterate over txt fils inside $QUEUE_PATH
for queue_file in $QUEUE_PATH/*.txt; do
    # Check if some other auto-youtube-dl instance already iterated further
    # TODO: Fix race conditions
    [ -f $queue_file ] || break

    { read -r video_url; read -r cmds; read -r opts; } <<<"$(<$queue_file)"
    mv -f "$queue_file" "${queue_file%.txt}.used"

    filename=`basename "$queue_file"`
    echo "`mydate` -------------------- $filename $cmds $opts"

    # User wants to run some code?
    [ ! -z "$cmds" ] && eval "$cmds"

    # User wants to change youtube-dl opts?
    if [ ! -z "$opts" ]; then
        YOPTIONS=( `echo "$opts" "${OPTIONS[@]}" | sed 's/ -/#-/g' | tr '#' '\n' | awk '!a[$1]++'` )
    else
        YOPTIONS=( "${OPTIONS[@]}" )
    fi

    # Will be left with this value when explicit query of video's title fails
    OUTNAME="$YDL_NAME_PATTERN"

    # Get video's title and duration
    while (( TITLERETRY++ < TITLEMAXRETRIES )); do
        # Run youtube-dl in background so that main process can still receive signals
        youtube-dl "${TITLE_DURATION_OPTIONS[@]}" "$video_url" > /tmp/ydl.$MAIN_PID &
        wait $!
        { read -r vtitle; read -r vduration; } <<<"$(</tmp/ydl.$MAIN_PID)"
        rm -f /tmp/ydl.$MAIN_PID

        : "${vduration:=--:--}"

        if [ ! -z "$vtitle" ]; then
            OUTNAME=`echo "$vtitle" | sed -e 's/[^a-zA-Z0-9._-][^a-zA-Z0-9._-]*/_/g' -e 's/_*$//' -e 's/^_*//'`.'%(ext)s'
            break;
        fi

        echo -e "`mydate` Prefetch of title and duration for <<${CI_GREEN}${filename}${_RST_}>> erroneously stopped"\
                        "[attempt ${CI_GREEN}#${TITLERETRY}${_RST_} / $TITLEMAXRETRIES]"

        sleep $SLEEP_TIME &
        wait $!
    done
    TITLERETRY=0

    # Append video's title and duration to the queue file
    echo -e "$video_url\\n$cmds\\n$opts\\n$vtitle $vduration" > "${queue_file%.txt}.used"
    echo "$queue_file" > "/tmp/ydlstart.$MAIN_PID"

    # Output a main message, emphasized by red color, containing title, duration and a video id
    urlid="${video_url##*/}"
    urlid="${urlid#*=}"
    urlid=`echo "$urlid" | sed -e 's/index=[0-9]*//' -e 's/list=[a-zA-Z0-9_\-]*//' -e 's/.*v=//' -e 's/&//g'`
    echo -e "`mydate` ${CI_RED}\`$vtitle'${_RST_} [${C_CYAN}${vduration}s${_RST_}] : $urlid\n"

    START_TIME=`timestamp`
    while (( RETRY ++ < MAXRETRIES )); do
        MSG="Repeating (try #$RETRY) download of <<${CI_GREEN}${filename}${_RST_}>>"
        if [ "$RETRY" = "1" ]; then
            MSG="${CI_GREEN}STARTING$_RST_ download of <<${CI_GREEN}${filename}${_RST_}>>"
        fi

        echo -e "`mydate` $MSG with the command:"\
        youtube-dl "${YOPTIONS[@]}" -o "$OUTPUT_VIDEO_PATH/$OUTNAME" "$CI_BLUE$video_url$_RST_"
        youtube-dl "${YOPTIONS[@]}" -o "$OUTPUT_VIDEO_PATH/$OUTNAME" "$video_url" &

        YDL_PID=$!
        echo "`mydate` youtube-dl PID is $YDL_PID"
        echo "$YDL_PID" > /tmp/ydlpid.$MAIN_PID

        if wait $YDL_PID; then
            DOWNLOAD_TIME=`timestamp`
            (( DOWNLOAD_TIME = (DOWNLOAD_TIME - START_TIME) / 60 ))
            echo -e "`mydate` ${C_YELLOW}Download of <<$filename>> successful"\
                    "(# of attempts: $RETRY, time: ${DOWNLOAD_TIME}m)$_RST_"
            RETRY=0
            break
        else
            echo -e "`mydate` Download of <<${CI_GREEN}${filename}${_RST_}>>"\
                            "halted at attempt ${CI_GREEN}${RETRY}${_RST_} / $MAXRETRIES"

            if [ -f /tmp/ydlpid.$MAIN_PID ]; then
                sleep $SLEEP_TIME &
                wait $!
            else
                echo -e "`mydate` ${CI_GREEN}[Intended restart]${_RST_}"
            fi
        fi
    done
done

move_finished

exit 0

