#!/bin/bash

DOWNLOAD_TESTS="age_restriction|download|subtitles|write_annotations|iqiyi_sdk_interpreter|youtube_lists"

test_set=""
multiprocess_args=""

case "$YTDL_TEST_SET" in
    core)
        test_set="-I test_($DOWNLOAD_TESTS)\.py"
    ;;
    download)
        test_set="-I test_(?!$DOWNLOAD_TESTS).+\.py"
        multiprocess_args="--processes=4 --process-timeout=540"
    ;;
    *)
        break
    ;;
esac

nosetests test --verbose $test_set $multiprocess_args
