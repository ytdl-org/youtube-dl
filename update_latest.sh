#/bins/sh
set -e

version="$1"

if [ -z "$version" ]; then
	echo "Usage: $0 version"
	exit 1
fi

cd "$(dirname $(readlink -f $0))"

ln -sf --no-target-directory ../downloads/$version latest/directory
for f in $(ls "downloads/$version/"); do \
    ln -sf --no-target-directory "../downloads/$version/$f" latest/$(echo $f | sed -e "s@-$version@@")
done
ln -sf --no-target-directory "downloads/$version" "downloads/latest"
echo -n "$version" > latest/version

