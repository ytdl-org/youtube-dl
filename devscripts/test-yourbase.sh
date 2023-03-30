#!/bin/bash

# Only run in docker container
# Run initial test with nosetest and yourbase
/app/devscripts/run_tests.sh

# Edit some files
echo "print('Hello World')" >> youtube_dl/extractor/buzzfeed.py

# Run test again
/app/devscripts/run_tests.sh
