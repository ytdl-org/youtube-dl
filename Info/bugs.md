# BUGS

Bugs and suggestions should be reported at: <https://github.com/ytdl-org/youtube-dl/issues>. Unless you were prompted to or there is another pertinent reason (e.g. GitHub fails to accept the bug report), please do not send bug reports via personal email. For discussions, join us in the IRC channel [#youtube-dl](irc://chat.freenode.net/#youtube-dl) on freenode ([webchat](https://webchat.freenode.net/?randomnick=1&channels=youtube-dl)).

**Please include the full output of youtube-dl when run with `-v`**, i.e. **add** `-v` flag to **your command line**, copy the **whole** output and post it in the issue body wrapped in \`\`\` for better formatting. It should look similar to this:
```
$ youtube-dl -v <your command line>
[debug] System config: []
[debug] User config: []
[debug] Command-line args: [u'-v', u'https://www.youtube.com/watch?v=BaW_jenozKcj']
[debug] Encodings: locale cp1251, fs mbcs, out cp866, pref cp1251
[debug] youtube-dl version 2015.12.06
[debug] Git HEAD: 135392e
[debug] Python version 2.6.6 - Windows-2003Server-5.2.3790-SP2
[debug] exe versions: ffmpeg N-75573-g1d0487f, ffprobe N-75573-g1d0487f, rtmpdump 2.4
[debug] Proxy map: {}
...
```
**Do not post screenshots of verbose logs; only plain text is acceptable.**

The output (including the first lines) contains important debugging information. Issues without the full output are often not reproducible and therefore do not get solved in short order, if ever.

Please re-read your issue once again to avoid a couple of common mistakes (you can and should use this as a checklist):

### Is the description of the issue itself sufficient?

We often get issue reports that we cannot really decipher. While in most cases we eventually get the required information after asking back multiple times, this poses an unnecessary drain on our resources. Many contributors, including myself, are also not native speakers, so we may misread some parts.

So please elaborate on what feature you are requesting, or what bug you want to be fixed. Make sure that it's obvious

- What the problem is
- How it could be fixed
- How your proposed solution would look like

If your report is shorter than two lines, it is almost certainly missing some of these, which makes it hard for us to respond to it. We're often too polite to close the issue outright, but the missing info makes misinterpretation likely. As a committer myself, I often get frustrated by these issues, since the only possible way for me to move forward on them is to ask for clarification over and over.

For bug reports, this means that your report should contain the *complete* output of youtube-dl when called with the `-v` flag. The error message you get for (most) bugs even says so, but you would not believe how many of our bug reports do not contain this information.

If your server has multiple IPs or you suspect censorship, adding `--call-home` may be a good idea to get more diagnostics. If the error is `ERROR: Unable to extract ...` and you cannot reproduce it from multiple countries, add `--dump-pages` (warning: this will yield a rather large output, redirect it to the file `log.txt` by adding `>log.txt 2>&1` to your command-line) or upload the `.dump` files you get when you add `--write-pages` [somewhere](https://gist.github.com/).

**Site support requests must contain an example URL**. An example URL is a URL you might want to download, like `https://www.youtube.com/watch?v=BaW_jenozKc`. There should be an obvious video present. Except under very special circumstances, the main page of a video service (e.g. `https://www.youtube.com/`) is *not* an example URL.

###  Are you using the latest version?

Before reporting any issue, type `youtube-dl -U`. This should report that you're up-to-date. About 20% of the reports we receive are already fixed, but people are using outdated versions. This goes for feature requests as well.

###  Is the issue already documented?

Make sure that someone has not already opened the issue you're trying to open. Search at the top of the window or browse the [GitHub Issues](https://github.com/ytdl-org/youtube-dl/search?type=Issues) of this repository. If there is an issue, feel free to write something along the lines of "This affects me as well, with version 2015.01.01. Here is some more information on the issue: ...". While some issues may be old, a new post into them often spurs rapid activity.

###  Why are existing options not enough?

Before requesting a new feature, please have a quick peek at [the list of supported options](https://github.com/ytdl-org/youtube-dl/blob/master/README.md#options). Many feature requests are for features that actually exist already! Please, absolutely do show off your work in the issue report and detail how the existing similar options do *not* solve your problem.

###  Is there enough context in your bug report?

People want to solve problems, and often think they do us a favor by breaking down their larger problems (e.g. wanting to skip already downloaded files) to a specific request (e.g. requesting us to look whether the file exists before downloading the info page). However, what often happens is that they break down the problem into two steps: One simple, and one impossible (or extremely complicated one).

We are then presented with a very complicated request when the original problem could be solved far easier, e.g. by recording the downloaded video IDs in a separate file. To avoid this, you must include the greater context where it is non-obvious. In particular, every feature request that does not consist of adding support for a new site should contain a use case scenario that explains in what situation the missing feature would be useful.

###  Does the issue involve one problem, and one problem only?

Some of our users seem to think there is a limit of issues they can or should open. There is no limit of issues they can or should open. While it may seem appealing to be able to dump all your issues into one ticket, that means that someone who solves one of your issues cannot mark the issue as closed. Typically, reporting a bunch of issues leads to the ticket lingering since nobody wants to attack that behemoth, until someone mercifully splits the issue into multiple ones.

In particular, every site support request issue should only pertain to services at one site (generally under a common domain, but always using the same backend technology). Do not request support for vimeo user videos, White house podcasts, and Google Plus pages in the same issue. Also, make sure that you don't post bug reports alongside feature requests. As a rule of thumb, a feature request does not include outputs of youtube-dl that are not immediately related to the feature at hand. Do not post reports of a network error alongside the request for a new video service.

###  Is anyone going to need the feature?

Only post features that you (or an incapacitated friend you can personally talk to) require. Do not post features because they seem like a good idea. If they are really useful, they will be requested by someone who requires them.

###  Is your question about youtube-dl?

It may sound strange, but some bug reports we receive are completely unrelated to youtube-dl and relate to a different, or even the reporter's own, application. Please make sure that you are actually using youtube-dl. If you are using a UI for youtube-dl, report the bug to the maintainer of the actual application providing the UI. On the other hand, if your UI for youtube-dl fails in some way you believe is related to youtube-dl, by all means, go ahead and report the bug.
