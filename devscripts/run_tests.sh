#!/bin/bash

DOWNLOAD_TESTS="age_restriction|download|subtitles|write_annotations|iqiyi_sdk_interpreter"

test_set=""

case "$YTDL_TEST_SET" in
    core)
        test_set="-I test_($DOWNLOAD_TESTS)\.py"
    ;;
    download)
        test_set="-I test_(?!$DOWNLOAD_TESTS).+\.py"
    ;;
    *)
        break
    ;;
esac

nosetests test --verbose $test_set
