# youtube-dl

This fork of <http://rg3.github.com/youtube-dl/> adds SOCKS4/SOCKS5 support
using the standard convention of environment variables:

    socks_proxy=http://127.0.0.1:9999 youtube-dl ...

The actual SOCKS code was taken from <https://gist.github.com/869791>
