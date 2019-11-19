[![Build Status](https://travis-ci.org/ytdl-org/youtube-dl.svg?branch=master)](https://travis-ci.org/ytdl-org/youtube-dl)

youtube-dl - download videos from youtube.com or other video platforms

# INSTALLATION

To install it right away for all UNIX users (Linux, macOS, etc.), type:

    sudo curl -L https://yt-dl.org/downloads/latest/youtube-dl -o /usr/local/bin/youtube-dl
    sudo chmod a+rx /usr/local/bin/youtube-dl

If you do not have curl, you can alternatively use a recent wget:

    sudo wget https://yt-dl.org/downloads/latest/youtube-dl -O /usr/local/bin/youtube-dl
    sudo chmod a+rx /usr/local/bin/youtube-dl

Windows users can [download an .exe file](https://yt-dl.org/latest/youtube-dl.exe) and place it in any location on their [PATH](https://en.wikipedia.org/wiki/PATH_%28variable%29) except for `%SYSTEMROOT%\System32` (e.g. **do not** put in `C:\Windows\System32`).

You can also use pip:

    sudo -H pip install --upgrade youtube-dl
    
This command will update youtube-dl if you have already installed it. See the [pypi page](https://pypi.python.org/pypi/youtube_dl) for more information.

macOS users can install youtube-dl with [Homebrew](https://brew.sh/):

    brew install youtube-dl

Or with [MacPorts](https://www.macports.org/):

    sudo port install youtube-dl

Alternatively, refer to the [developer instructions](#developer-instructions) for how to check out and work with the git repository. For further options, including PGP signatures, see the [youtube-dl Download Page](https://ytdl-org.github.io/youtube-dl/download.html). 

# DESCRIPTION
**youtube-dl** is a command-line program to download videos from YouTube.com and a few more sites. It requires the Python interpreter, version 2.6, 2.7, or 3.2+, and it is not platform specific. It should work on your Unix box, on Windows or on macOS. It is released to the public domain, which means you can modify it, redistribute it or use it however you like.

    youtube-dl [OPTIONS] URL [URL...]

- [OPTIONS](Info/options.md)
- [CONFIGURATION](Info/configuration.md)
- [OUTPUT TEMPLATE](Info/output-template.md)
- [FORMAT SELECTION](Info/format-selection.md)
- [VIDEO SELECTION](Info/video-selection.md)
- [FAQ](Info/faq.md)
- [DEVELOPER INSTRUCTIONS](Info/developer-instructions.md)
- [EMBEDDING YOUTUBE-DL](Info/embedding-youtube-dl.md)
- [BUGS](Info/bugs.md)

# COPYRIGHT

youtube-dl is released into the public domain by the copyright holders.

This README file was originally written by [Daniel Bolton](https://github.com/dbbolton) and is likewise released into the public domain.
