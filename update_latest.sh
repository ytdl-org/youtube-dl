#/bins/sh
set -e

version="$1"

if [ -z "$version" ]; then
	echo "Usage: $0 version"
	exit 1
fi

cd "$(dirname $(readlink -f $0))"

echo -n "$version" > latest_version

echo -e "RewriteEngine On" > downloads/.htaccess
echo -e "RewriteRule ^$ https://github.com/ytdl-org/youtube-dl/releases" >> downloads/.htaccess
echo -e "RewriteRule ^(\d{4}\.\d{2}\.\d{2}(?:\.\d+)?/?)$ https://github.com/ytdl-org/youtube-dl/releases/tag/\$1" >> downloads/.htaccess
echo -e "RewriteRule ^(\d{4}\.\d{2}\.\d{2}(?:\.\d+)?/.+)$ https://github.com/ytdl-org/youtube-dl/releases/download/\$1" >> downloads/.htaccess
echo -e "RewriteRule latest(.*) /downloads/$1\$1 [L,R=302]" >> downloads/.htaccess
