youtube-dl
==========
Download videos from youtube.com or other video platforms

Description
-----------
**youtube-dl** is a small command-line program to download videos from
YouTube.com and many other online video sites. It requires the Python interpreter, version
2.6, 2.7, or 3.3+, and it is not platform specific. It should work on
your Unix box, on Windows or on Mac OS X. It is released to the public domain,
which means you can modify it, redistribute it or use it however you like.

Getting youtube-dl
------------------
To install it right away for all UNIX users (Linux, OS X, etc.), type:

    sudo curl https://yt-dl.org/latest/youtube-dl -o /usr/local/bin/youtube-dl
    sudo chmod a+x /usr/local/bin/youtube-dl

If you do not have curl, you can alternatively use a recent wget:

    sudo wget https://yt-dl.org/downloads/2014.05.13/youtube-dl -O /usr/local/bin/youtube-dl
    sudo chmod a+x /usr/local/bin/youtube-dl

Windows users can [download a .exe file](https://yt-dl.org/latest/youtube-dl.exe) and place it in their home directory or any other location on their [PATH](http://en.wikipedia.org/wiki/PATH_%28variable%29).

Alternatively, refer to the developer instructions below for how to check out and work with the git repository. For further options, including PGP signatures, see https://rg3.github.io/youtube-dl/download.html .

Features
--------
* youtube-dl can currently download from over 300 sites. (Type `youtube-dl --list-extractors` or `youtube-dl --extractor-description` for more info.
* It has support for http(s) proxies and various network configurations
* It can extract the audio from downloaded videos using `ffmpeg` or `avconv`, as well as choosing from available formats
* It has support for downloading playlists, filename lists, channels, users and more
* It can output files to custom locations, and rename using templates based on filename, format etc.
This is only a small sample of what youtube-dl can do. Type `youtube-dl --help` for a comprehensive list of options
 
FAQ
---

### Can you please put the -b option back?

Most people asking this question are not aware that youtube-dl now defaults to downloading the highest available quality as reported by YouTube, which will be 1080p or 720p in some cases, so you no longer need the `-b` option. For some specific videos, maybe YouTube does not report them to be available in a specific high quality format you're interested in. In that case, simply request it with the `-f` option and youtube-dl will try to download it.

### I get HTTP error 402 when trying to download a video. What's this?

Apparently YouTube requires you to pass a CAPTCHA test if you download too much. We're [considering to provide a way to let you solve the CAPTCHA](https://github.com/rg3/youtube-dl/issues/154), but at the moment, your best course of action is pointing a webbrowser to the youtube URL, solving the CAPTCHA, and restart youtube-dl.

### I have downloaded a video but how can I play it?

Once the video is fully downloaded, use any video player, such as [vlc](http://www.videolan.org) or [mplayer](http://www.mplayerhq.hu/).

### The links provided by youtube-dl -g are not working anymore

The URLs youtube-dl outputs require the downloader to have the correct cookies. Use the `--cookies` option to write the required cookies into a file, and advise your downloader to read cookies from that file. Some sites also require a common user agent to be used, use `--dump-user-agent` to see the one in use by youtube-dl.

### ERROR: no fmt_url_map or conn information found in video info

youtube has switched to a new video info format in July 2011 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

### ERROR: unable to download video ###

youtube requires an additional signature since September 2012 which is not supported by old versions of youtube-dl. You can update youtube-dl with `sudo youtube-dl --update`.

### SyntaxError: Non-ASCII character ###

The error

    File "youtube-dl", line 2
    SyntaxError: Non-ASCII character '\x93' ...

means you're using an outdated version of Python. Please update to Python 2.6 or 2.7.

### What is this binary file? Where has the code gone?

Since June 2012 (#342) youtube-dl is packed as an executable zipfile, simply unzip it (might need renaming to `youtube-dl.zip` first on some systems) or clone the git repository, as laid out above. If you modify the code, you can run it by executing the `__main__.py` file. To recompile the executable, run `make youtube-dl`.

### The exe throws a *Runtime error from Visual C++*

To run the exe you need to install first the [Microsoft Visual C++ 2008 Redistributable Package](http://www.microsoft.com/en-us/download/details.aspx?id=29).

Developing
----------

Most users do not need to build youtube-dl and can [download the builds](http://rg3.github.io/youtube-dl/download.html) or get them from their distribution.

To run youtube-dl as a developer, you don't need to build anything either. Simply execute

    python -m youtube_dl

To run the test, simply invoke your favorite test runner, or execute a test file directly; any of the following work:

    python -m unittest discover
    python test/test_download.py
    nosetests

If you want to create a build of youtube-dl yourself, you'll need

* python
* make
* pandoc
* zip
* nosetests

### Adding support for a new site

If you want to add support for a new site, you can follow this quick list (assuming your service is called `yourextractor`):

1. [Fork this repository](https://github.com/rg3/youtube-dl/fork)
2. Check out the source code with `git clone git@github.com:YOUR_GITHUB_USERNAME/youtube-dl.git`
3. Start a new git branch with `cd youtube-dl; git checkout -b yourextractor`
4. Start with this simple template and save it to `youtube_dl/extractor/yourextractor.py`:

        # coding: utf-8
        from __future__ import unicode_literals

        import re

        from .common import InfoExtractor
        
        
        class YourExtractorIE(InfoExtractor):
            _VALID_URL = r'https?://(?:www\.)?yourextractor\.com/watch/(?P<id>[0-9]+)'
            _TEST = {
                'url': 'http://yourextractor.com/watch/42',
                'md5': 'TODO: md5 sum of the first 10KiB of the video file',
                'info_dict': {
                    'id': '42',
                    'ext': 'mp4',
                    'title': 'Video title goes here',
                    # TODO more properties, either as:
                    # * A value
                    # * MD5 checksum; start the string with md5:
                    # * A regular expression; start the string with re:
                    # * Any Python type (for example int or float)
                }
            }

            def _real_extract(self, url):
                mobj = re.match(self._VALID_URL, url)
                video_id = mobj.group('id')

                # TODO more code goes here, for example ...
                webpage = self._download_webpage(url, video_id)
                title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title')

                return {
                    'id': video_id,
                    'title': title,
                    # TODO more properties (see youtube_dl/extractor/common.py)
                }


5. Add an import in [`youtube_dl/extractor/__init__.py`](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/__init__.py).
6. Run `python test/test_download.py TestDownload.test_YourExtractor`. This *should fail* at first, but you can continually re-run it until you're done.
7. Have a look at [`youtube_dl/common/extractor/common.py`](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/common.py) for possible helper methods and a [detailed description of what your extractor should return](https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/common.py#L38). Add tests and code for as many as you want.
8. If you can, check the code with [pyflakes](https://pypi.python.org/pypi/pyflakes) (a good idea) and [pep8](https://pypi.python.org/pypi/pep8) (optional, ignore E501).
9. When the tests pass, [add](https://www.kernel.org/pub/software/scm/git/docs/git-add.html) the new files and [commit](https://www.kernel.org/pub/software/scm/git/docs/git-commit.html) them and [push](https://www.kernel.org/pub/software/scm/git/docs/git-push.html) the result, like this:

        $ git add youtube_dl/extractor/__init__.py
        $ git add youtube_dl/extractor/yourextractor.py
        $ git commit -m '[yourextractor] Add new extractor'
        $ git push origin yourextractor

10. Finally, [create a pull request](https://help.github.com/articles/creating-a-pull-request). We'll then review and merge it.

In any case, thank you very much for your contributions!

Bugs
----

Bugs and suggestions should be reported at: <https://github.com/rg3/youtube-dl/issues> . Unless you were prompted so or there is another pertinent reason (e.g. GitHub fails to accept the bug report), please do not send bug reports via personal email.

Please include the full output of the command when run with `--verbose`. The output (including the first lines) contain important debugging information. Issues without the full output are often not reproducible and therefore do not get solved in short order, if ever.

For discussions, join us in the irc channel #youtube-dl on freenode.

When you submit a request, please re-read it once to avoid a couple of mistakes (you can and should use this as a checklist):

### Is the description of the issue itself sufficient?

We often get issue reports that we cannot really decipher. While in most cases we eventually get the required information after asking back multiple times, this poses an unnecessary drain on our resources. Many contributors, including myself, are also not native speakers, so we may misread some parts.

So please elaborate on what feature you are requesting, or what bug you want to be fixed. Make sure that it's obvious

- What the problem is
- How it could be fixed
- How your proposed solution would look like

If your report is shorter than two lines, it is almost certainly missing some of these, which makes it hard for us to respond to it. We're often too polite to close the issue outright, but the missing info makes misinterpretation likely. As a commiter myself, I often get frustrated by these issues, since the only possible way for me to move forward on them is to ask for clarification over and over.

For bug reports, this means that your report should contain the *complete* output of youtube-dl when called with the -v flag. The error message you get for (most) bugs even says so, but you would not believe how many of our bug reports do not contain this information.

Site support requests **must contain an example URL**. An example URL is a URL you might want to download, like http://www.youtube.com/watch?v=BaW_jenozKc . There should be an obvious video present. Except under very special circumstances, the main page of a video service (e.g. http://www.youtube.com/ ) is *not* an example URL.

###  Are you using the latest version?

Before reporting any issue, type youtube-dl -U. This should report that you're up-to-date. About 20% of the reports we receive are already fixed, but people are using outdated versions. This goes for feature requests as well.

###  Is the issue already documented?

Make sure that someone has not already opened the issue you're trying to open. Search at the top of the window or at https://github.com/rg3/youtube-dl/search?type=Issues . If there is an issue, feel free to write something along the lines of "This affects me as well, with version 2015.01.01. Here is some more information on the issue: ...". While some issues may be old, a new post into them often spurs rapid activity.

###  Why are existing options not enough?

Before requesting a new feature, please have a quick peek at [the list of supported options](https://github.com/rg3/youtube-dl/blob/master/README.md#synopsis). Many feature requests are for features that actually exist already! Please, absolutely do show off your work in the issue report and detail how the existing similar options do *not* solve your problem.

###  Is there enough context in your bug report?

People want to solve problems, and often think they do us a favor by breaking down their larger problems (e.g. wanting to skip already downloaded files) to a specific request (e.g. requesting us to look whether the file exists before downloading the info page). However, what often happens is that they break down the problem into two steps: One simple, and one impossible (or extremely complicated one).

We are then presented with a very complicated request when the original problem could be solved far easier, e.g. by recording the downloaded video IDs in a separate file. To avoid this, you must include the greater context where it is non-obvious. In particular, every feature request that does not consist of adding support for a new site should contain a use case scenario that explains in what situation the missing feature would be useful.

###  Does the issue involve one problem, and one problem only?

Some of our users seem to think there is a limit of issues they can or should open. There is no limit of issues they can or should open. While it may seem appealing to be able to dump all your issues into one ticket, that means that someone who solves one of your issues cannot mark the issue as closed. Typically, reporting a bunch of issues leads to the ticket lingering since nobody wants to attack that behemoth, until someone mercifully splits the issue into multiple ones.

In particular, every site support request issue should only pertain to services at one site (generally under a common domain, but always using the same backend technology). Do not request support for vimeo user videos, Whitehouse podcasts, and Google Plus pages in the same issue. Also, make sure that you don't post bug reports alongside feature requests. As a rule of thumb, a feature request does not include outputs of youtube-dl that are not immediately related to the feature at hand. Do not post reports of a network error alongside the request for a new video service.

###  Is anyone going to need the feature?

Only post features that you (or an incapicated friend you can personally talk to) require. Do not post features because they seem like a good idea. If they are really useful, they will be requested by someone who requires them.

###  Is your question about youtube-dl?

It may sound strange, but some bug reports we receive are completely unrelated to youtube-dl and relate to a different or even the reporter's own application. Please make sure that you are actually using youtube-dl. If you are using a UI for youtube-dl, report the bug to the maintainer of the actual application providing the UI. On the other hand, if your UI for youtube-dl fails in some way you believe is related to youtube-dl, by all means, go ahead and report the bug.

License
-------

youtube-dl is released into the public domain by the copyright holders.

This README file was originally written by Daniel Bolton (<https://github.com/dbbolton>), reformatted by Felix Friedlander (<felixphew0@gmail.com>) and is likewise released into the public domain.
