## Please follow the guide below

- You will be asked some questions and requested to provide some information, please read them **carefully** and answer honestly
- Put an `x` into all the boxes [ ] relevant to your *issue* (like that [x])
- Use *Preview* tab to see how your issue will actually look like

---

### Make sure you are using the *latest* version: run `youtube-dl --version` and ensure your version is *2016.08.17*. If it's not read [this FAQ entry](https://github.com/rg3/youtube-dl/blob/master/README.md#how-do-i-update-youtube-dl) and update. Issues with outdated version will be rejected.
- [ ] I've **verified** and **I assure** that I'm running youtube-dl **2016.08.17**

### Before submitting an *issue* make sure you have:
- [ ] At least skimmed through [README](https://github.com/rg3/youtube-dl/blob/master/README.md) and **most notably** [FAQ](https://github.com/rg3/youtube-dl#faq) and [BUGS](https://github.com/rg3/youtube-dl#bugs) sections
- [ ] [Searched](https://github.com/rg3/youtube-dl/search?type=Issues) the bugtracker for similar issues including closed ones

### What is the purpose of your *issue*?
- [ ] Bug report (encountered problems with youtube-dl)
- [ ] Site support request (request for adding support for a new site)
- [ ] Feature request (request for a new functionality)
- [ ] Question
- [ ] Other

---

### The following sections concretize particular purposed issues, you can erase any section (the contents between triple ---) not applicable to your *issue*

---

### If the purpose of this *issue* is a *bug report*, *site support request* or you are not completely sure provide the full verbose output as follows:

Add `-v` flag to **your command line** you run youtube-dl with, copy the **whole** output and insert it here. It should look similar to one below (replace it with **your** log inserted between triple ```):
```
$ youtube-dl -v <your command line>
[debug] System config: []
[debug] User config: []
[debug] Command-line args: [u'-v', u'http://www.youtube.com/watch?v=BaW_jenozKcj']
[debug] Encodings: locale cp1251, fs mbcs, out cp866, pref cp1251
[debug] youtube-dl version 2016.08.17
[debug] Python version 2.7.11 - Windows-2003Server-5.2.3790-SP2
[debug] exe versions: ffmpeg N-75573-g1d0487f, ffprobe N-75573-g1d0487f, rtmpdump 2.4
[debug] Proxy map: {}
...
<end of log>
```

---

### If the purpose of this *issue* is a *site support request* please provide all kinds of example URLs support for which should be included (replace following example URLs by **yours**):
- Single video: https://www.youtube.com/watch?v=BaW_jenozKc
- Single video: https://youtu.be/BaW_jenozKc
- Playlist: https://www.youtube.com/playlist?list=PL4lCao7KL_QFVb7Iudeipvc2BCavECqzc

---

### Description of your *issue*, suggested solution and other information

Explanation of your *issue* in arbitrary form goes here. Please make sure the [description is worded well enough to be understood](https://github.com/rg3/youtube-dl#is-the-description-of-the-issue-itself-sufficient). Provide as much context and examples as possible.
If work on your *issue* required an account credentials please provide them or explain how one can obtain them.
