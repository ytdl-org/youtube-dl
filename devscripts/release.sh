#!/bin/sh

if [ -z "$1" ]; then echo "ERROR: specify version number like this: $0 1994.09.06"; exit 1; fi
version="$1"
if [ ! -z "`git tag | grep "$version"`" ]; then echo 'ERROR: version already present'; exit 1; fi
if [ ! -z "`git status --porcelain`" ]; then echo 'ERROR: the working directory is not clean; commit or stash changes'; exit 1; fi
sed -i "s/__version__ = '.*'/__version__ = '$version'/" youtube_dl/__init__.py
make all
git add -A
git commit -m "release $version"
git tag -m "Release $version" "$version"