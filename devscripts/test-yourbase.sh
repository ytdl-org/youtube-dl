#!/bin/bash

# Only run in docker container
# Run initial test with nosetest and yourbase
echo "\n---------Running initial test------------\n\n"
/app/devscripts/run_tests.sh

# Edit some files
echo "\n---------Editing files------------\n\n"
echo "print('Hello World')" >> youtube_dl/extractor/buzzfeed.py

# Run test again
echo "\n--------Running test again------------\n\n"
/app/devscripts/run_tests.sh
