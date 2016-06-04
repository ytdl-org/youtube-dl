#/bins/sh
set -e

version="$1"

if [ -z "$version" ]; then
	echo "Usage: $0 version"
	exit 1
fi

cd "$(dirname $(readlink -f $0))"

echo -n "$version" > latest_version
ln -sf downloads/latest downloads/$1

