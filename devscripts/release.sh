#!/bin/bash

# IMPORTANT: the following assumptions are made
# * the GH repo is on the origin remote
# * the gh-pages branch is named so locally
# * the git config user.signingkey is properly set

# You will need
# pip install coverage nose rsa

# TODO
# release notes
# make hash on local files

set -e

skip_tests=true
if [ "$1" = '--run-tests' ]; then
    skip_tests=false
    shift
fi

if [ -z "$1" ]; then echo "ERROR: specify version number like this: $0 1994.09.06"; exit 1; fi
version="$1"
if [ ! -z "`git tag | grep "$version"`" ]; then echo 'ERROR: version already present'; exit 1; fi
if [ ! -z "`git status --porcelain | grep -v CHANGELOG`" ]; then echo 'ERROR: the working directory is not clean; commit or stash changes'; exit 1; fi
useless_files=$(find youtube_dl -type f -not -name '*.py')
if [ ! -z "$useless_files" ]; then echo "ERROR: Non-.py files in youtube_dl: $useless_files"; exit 1; fi
if [ ! -f "updates_key.pem" ]; then echo 'ERROR: updates_key.pem missing'; exit 1; fi

/bin/echo -e "\n### First of all, testing..."
make cleanall
if $skip_tests ; then
    echo 'SKIPPING TESTS'
else
    nosetests --verbose --with-coverage --cover-package=youtube_dl --cover-html test --stop || exit 1
fi

/bin/echo -e "\n### Changing version in version.py..."
sed -i "s/__version__ = '.*'/__version__ = '$version'/" youtube_dl/version.py

/bin/echo -e "\n### Committing CHANGELOG README.md and youtube_dl/version.py..."
make README.md
git add CHANGELOG README.md youtube_dl/version.py
git commit -m "release $version"

/bin/echo -e "\n### Now tagging, signing and pushing..."
git tag -s -m "Release $version" "$version"
git show "$version"
read -p "Is it good, can I push? (y/n) " -n 1
if [[ ! $REPLY =~ ^[Yy]$ ]]; then exit 1; fi
echo
MASTER=$(git rev-parse --abbrev-ref HEAD)
git push origin $MASTER:master
git push origin "$version"

/bin/echo -e "\n### OK, now it is time to build the binaries..."
REV=$(git rev-parse HEAD)
make youtube-dl youtube-dl.tar.gz
read -p "VM running? (y/n) " -n 1
wget "http://localhost:8142/build/rg3/youtube-dl/youtube-dl.exe?rev=$REV" -O youtube-dl.exe
mkdir -p "build/$version"
mv youtube-dl youtube-dl.exe "build/$version"
mv youtube-dl.tar.gz "build/$version/youtube-dl-$version.tar.gz"
RELEASE_FILES="youtube-dl youtube-dl.exe youtube-dl-$version.tar.gz"
(cd build/$version/ && md5sum $RELEASE_FILES > MD5SUMS)
(cd build/$version/ && sha1sum $RELEASE_FILES > SHA1SUMS)
(cd build/$version/ && sha256sum $RELEASE_FILES > SHA2-256SUMS)
(cd build/$version/ && sha512sum $RELEASE_FILES > SHA2-512SUMS)
git checkout HEAD -- youtube-dl youtube-dl.exe

/bin/echo -e "\n### Signing and uploading the new binaries to yt-dl.org ..."
for f in $RELEASE_FILES; do gpg --passphrase-repeat 5 --detach-sig "build/$version/$f"; done
scp -r "build/$version" ytdl@yt-dl.org:html/tmp/
ssh ytdl@yt-dl.org "mv html/tmp/$version html/downloads/"
ssh ytdl@yt-dl.org "sh html/update_latest.sh $version"

/bin/echo -e "\n### Now switching to gh-pages..."
git clone --branch gh-pages --single-branch . build/gh-pages
ROOT=$(pwd)
(
    set -e
    ORIGIN_URL=$(git config --get remote.origin.url)
    cd build/gh-pages
    "$ROOT/devscripts/gh-pages/add-version.py" $version
    "$ROOT/devscripts/gh-pages/update-feed.py"
    "$ROOT/devscripts/gh-pages/sign-versions.py" < "$ROOT/updates_key.pem"
    "$ROOT/devscripts/gh-pages/generate-download.py"
    "$ROOT/devscripts/gh-pages/update-copyright.py"
    "$ROOT/devscripts/gh-pages/update-sites.py"
    git add *.html *.html.in update
    git commit -m "release $version"
    git push "$ROOT" gh-pages
    git push "$ORIGIN_URL" gh-pages
)
rm -rf build

make pypi-files
echo "Uploading to PyPi ..."
python setup.py sdist bdist_wheel upload
make clean

/bin/echo -e "\n### DONE!"
