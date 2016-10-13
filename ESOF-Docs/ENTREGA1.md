DESCRIPTION

youtube-dl is a command-line program to download videos from YouTube.com and a few more sites. It requires the Python interpreter, version 2.6, 2.7, or 3.2+, and it is not platform specific. It should work on your Unix box, on Windows or on Mac OS X. It is released to the public domain, which means you can modify it, redistribute it or use it however you like.
youtube-dl works fine on its own on most sites. However, if you want to convert video/audio, you'll need avconv or ffmpeg. On some sites - most notably YouTube - videos can be retrieved in a higher quality format without sound. youtube-dl will detect whether avconv/ffmpeg is present and automatically pick the best option.
By default youtube-dl tries to download the best available quality, i.e. if you want the best quality you don't need to pass any special options, youtube-dl will guess it for you by default.

Once the video is fully downloaded, use any video player, such as mpv, vlc or mplayer.
