#/bins/sh
set -e

version="$1"

ln -sf ../downloads/$version latest/directory
for f in $(ls "downloads/$version/"); do \
    ln -sf "../downloads/$version/$f" latest/$(echo $f | sed -e "s@-$version@@")
done
