:orphan:

YOUTUBE-DL(1)
*************

SYNOPSIS
========

**youtube-dl** [OPTIONS] URL [URL...]

DESCRIPTION
===========

**youtube-dl** is a small command-line program to download videos from
YouTube.com and a few more sites. It requires the Python interpreter, version
2.6, 2.7, or 3.3+, and it is not platform specific. It should work on
your Unix box, on Windows or on Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.

OPTIONS
=======
.. include:: options.rst.inc

CONFIGURATION
=============

You can configure youtube-dl by placing default arguments (such as ``--extract-audio --no-mtime`` to always extract the audio and not copy the mtime) into :file:`/etc/youtube-dl.conf` and/or :file:`~/.config/youtube-dl/config`. On Windows, the configuration file locations are :file:`%APPDATA%\\youtube-dl\\config.txt` and :file:`C:\Users\\<Yourname>\\youtube-dl.conf`.

OUTPUT TEMPLATE
===============

The ``-o`` option allows users to indicate a template for the output file names. The basic usage is not to set any template arguments when downloading a single file, like in ``youtube-dl -o funny_video.flv "http://some/video"``. However, it may contain special sequences that will be replaced when downloading each video. The special sequences have the format ``%(NAME)s``. To clarify, that is a percent symbol followed by a name in parenthesis, followed by a lowercase S. Allowed names are:

 - ``id``: The sequence will be replaced by the video identifier.
 - ``url``: The sequence will be replaced by the video URL.
 - ``uploader``: The sequence will be replaced by the nickname of the person who uploaded the video.
 - ``upload_date``: The sequence will be replaced by the upload date in YYYYMMDD format.
 - ``title``: The sequence will be replaced by the video title.
 - ``ext``: The sequence will be replaced by the appropriate extension (like flv or mp4).
 - ``epoch``: The sequence will be replaced by the Unix epoch when creating the file.
 - ``autonumber``: The sequence will be replaced by a five-digit number that will be increased with each download, starting at zero.
 - ``playlist``: The name or the id of the playlist that contains the video.
 - ``playlist_index``: The index of the video in the playlist, a five-digit number.

The current default template is ``%(title)s-%(id)s.%(ext)s``.

In some cases, you don't want special characters such as 中, spaces, or &, such as when transferring the downloaded filename to a Windows system or the filename through an 8bit-unsafe channel. In these cases, add the ``--restrict-filenames`` flag to get a shorter title::

    $ youtube-dl --get-filename -o "%(title)s.%(ext)s" BaW_jenozKc
    youtube-dl test video ''_ä↭𝕐.mp4    # All kinds of weird characters
    $ youtube-dl --get-filename -o "%(title)s.%(ext)s" BaW_jenozKc --restrict-filenames
    youtube-dl_test_video_.mp4          # A simple file name

VIDEO SELECTION
===============

Videos can be filtered by their upload date using the options ``--date``, ``--datebefore`` or ``--dateafter``, they accept dates in two formats:

 - Absolute dates: Dates in the format ``YYYYMMDD``.
 - Relative dates: Dates in the format ``(now|today)[+-][0-9](day|week|month|year)(s)?``

Examples::

    # Download only the videos uploaded in the last 6 months
    $ youtube-dl --dateafter now-6months

    # Download only the videos uploaded on January 1, 1970
    $ youtube-dl --date 19700101

    $ # will only download the videos uploaded in the 200x decade
    $ youtube-dl --dateafter 20000101 --datebefore 20091231

.. include:: faq.rst
