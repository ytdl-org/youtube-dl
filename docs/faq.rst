FAQ
===

Can you please put the -b option back?
--------------------------------------

Most people asking this question are not aware that youtube-dl now defaults to downloading the highest available quality as reported by YouTube, which will be 1080p or 720p in some cases, so you no longer need the `-b` option. For some specific videos, maybe YouTube does not report them to be available in a specific high quality format you're interested in. In that case, simply request it with the `-f` option and youtube-dl will try to download it.

I get HTTP error 402 when trying to download a video. What's this?
------------------------------------------------------------------

Apparently YouTube requires you to pass a CAPTCHA test if you download too much. We're [considering to provide a way to let you solve the CAPTCHA](https://github.com/rg3/youtube-dl/issues/154), but at the moment, your best course of action is pointing a webbrowser to the youtube URL, solving the CAPTCHA, and restart youtube-dl.

I have downloaded a video but how can I play it?
------------------------------------------------

Once the video is fully downloaded, use any video player, such as [vlc](http://www.videolan.org) or [mplayer](http://www.mplayerhq.hu/).

The links provided by youtube-dl -g are not working anymore
-----------------------------------------------------------

The URLs youtube-dl outputs require the downloader to have the correct cookies. Use the `--cookies` option to write the required cookies into a file, and advise your downloader to read cookies from that file. Some sites also require a common user agent to be used, use `--dump-user-agent` to see the one in use by youtube-dl.

ERROR: no fmt_url_map or conn information found in video info
-------------------------------------------------------------

youtube has switched to a new video info format in July 2011 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

ERROR: unable to download video
-------------------------------

youtube requires an additional signature since September 2012 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

SyntaxError: Non-ASCII character
--------------------------------

The error

    File "youtube-dl", line 2
    SyntaxError: Non-ASCII character '\x93' ...

means you're using an outdated version of Python. Please update to Python 2.6 or 2.7.

What is this binary file? Where has the code gone?
--------------------------------------------------

Since June 2012 (#342) youtube-dl is packed as an executable zipfile, simply unzip it (might need renaming to `youtube-dl.zip` first on some systems) or clone the git repository, as laid out above. If you modify the code, you can run it by executing the `__main__.py` file. To recompile the executable, run `make youtube-dl`.

The exe throws a *Runtime error from Visual C++*
------------------------------------------------

To run the exe you need to install first the [Microsoft Visual C++ 2008 Redistributable Package](http://www.microsoft.com/en-us/download/details.aspx?id=29).
