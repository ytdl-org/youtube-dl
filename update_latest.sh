#/bins/sh
set -e

version="$1"

if [ -z "$version" ]; then
	echo "Usage: $0 version"
	exit 1
fi

cd "$(dirname $(readlink -f $0))"

echo -n "$version" > latest_version
/bin/echo -e "RewriteEngine On\nRewriteRule ^(.*)$ /downloads/latest/$1 [L,R=302]" > latest/.htaccess
