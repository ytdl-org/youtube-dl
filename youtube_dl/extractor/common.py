import base64
import os
import re
import socket
import sys
import netrc

from ..utils import (
    compat_http_client,
    compat_urllib_error,
    compat_urllib_request,
    compat_str,

    clean_html,
    compiled_regex_type,
    ExtractorError,
    RegexNotFoundError,
    sanitize_filename,
    unescapeHTML,
)

class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information about the video (or videos) the URL refers to. This
    information includes the real video URL, the video title, author and
    others. The information is stored in a dictionary which is then
    passed to the FileDownloader. The FileDownloader processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The dictionaries must include the following fields:

    id:             Video identifier.
    url:            Final video URL.
    title:          Video title, unescaped.
    ext:            Video filename extension.

    Instead of url and ext, formats can also specified.

    The following fields are optional:

    format:         The video format, defaults to ext (used for --get-format)
    thumbnails:     A list of dictionaries (with the entries "resolution" and
                    "url") for the varying thumbnails
    thumbnail:      Full URL to a video thumbnail image.
    description:    One-line video description.
    uploader:       Full name of the video uploader.
    upload_date:    Video upload date (YYYYMMDD).
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location of the video.
    player_url:     SWF Player URL (used for rtmpdump).
    subtitles:      The subtitle file contents as a dictionary in the format
                    {language: subtitles}.
    view_count:     How many users have watched the video on the platform.
    urlhandle:      [internal] The urlHandle to be used to download the file,
                    like returned by urllib.request.urlopen
    age_limit:      Age restriction for the video, as an integer (years)
    formats:        A list of dictionaries for each format available, it must
                    be ordered from worst to best quality. Potential fields:
                    * url       Mandatory. The URL of the video file
                    * ext       Will be calculated from url if missing
                    * format    A human-readable description of the format
                                ("mp4 container with h264/opus").
                                Calculated from the format_id, width, height.
                                and format_note fields if missing.
                    * format_id A short description of the format
                                ("mp4_h264_opus" or "19")
                    * format_note Additional info about the format
                                ("3D" or "DASH video")
                    * width     Width of the video, if known
                    * height    Height of the video, if known
    webpage_url:    The url to the video webpage, if given to youtube-dl it
                    should allow to get the same result again. (It will be set
                    by YoutubeDL if it's missing)

    Unless mentioned otherwise, the fields should be Unicode strings.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.

    _real_extract() must return a *list* of information dictionaries as
    described above.

    Finally, the _WORKING attribute should be set to False for broken IEs
    in order to warn the users and skip the tests.
    """

    _ready = False
    _downloader = None
    _WORKING = True

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self.set_downloader(downloader)

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""

        # This does not use has/getattr intentionally - we want to know whether
        # we have cached the regexp for *this* class, whereas getattr would also
        # match the superclass
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        return cls._VALID_URL_RE.match(url) is not None

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        self.initialize()
        return self._real_extract(url)

    def set_downloader(self, downloader):
        """Sets the downloader for this IE."""
        self._downloader = downloader

    def _real_initialize(self):
        """Real initialization process. Redefine in subclasses."""
        pass

    def _real_extract(self, url):
        """Real extraction process. Redefine in subclasses."""
        pass

    @classmethod
    def ie_key(cls):
        """A string for getting the InfoExtractor with get_info_extractor"""
        return cls.__name__[:-2]

    @property
    def IE_NAME(self):
        return type(self).__name__[:-2]

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            self.to_screen(u'%s: %s' % (video_id, note))
        try:
            return compat_urllib_request.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is None:
                errnote = u'Unable to download webpage'
            raise ExtractorError(u'%s: %s' % (errnote, compat_str(err)), sys.exc_info()[2], cause=err)

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns a tuple (page content as string, URL handle) """

        # Strip hashes from the URL (#1038)
        if isinstance(url_or_request, (compat_str, str)):
            url_or_request = url_or_request.partition('#')[0]

        urlh = self._request_webpage(url_or_request, video_id, note, errnote)
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        m = re.match(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+\s*;\s*charset=(.+)', content_type)
        if m:
            encoding = m.group(1)
        else:
            m = re.search(br'<meta[^>]+charset=[\'"]?([^\'")]+)[ /\'">]',
                          webpage_bytes[:1024])
            if m:
                encoding = m.group(1).decode('ascii')
            else:
                encoding = 'utf-8'
        if self._downloader.params.get('dump_intermediate_pages', False):
            try:
                url = url_or_request.get_full_url()
            except AttributeError:
                url = url_or_request
            self.to_screen(u'Dumping request to ' + url)
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self._downloader.to_screen(dump)
        if self._downloader.params.get('write_pages', False):
            try:
                url = url_or_request.get_full_url()
            except AttributeError:
                url = url_or_request
            raw_filename = ('%s_%s.dump' % (video_id, url))
            filename = sanitize_filename(raw_filename, restricted=True)
            self.to_screen(u'Saving request to ' + filename)
            with open(filename, 'wb') as outf:
                outf.write(webpage_bytes)

        content = webpage_bytes.decode(encoding, 'replace')
        return (content, urlh)

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None):
        """ Returns the data of the page as a string """
        return self._download_webpage_handle(url_or_request, video_id, note, errnote)[0]

    def to_screen(self, msg):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        self._downloader.to_screen(u'[%s] %s' % (self.IE_NAME, msg))

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        self.to_screen(u'%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self.to_screen(u'%s: Downloading webpage' % video_id)

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self.to_screen(u'Confirming age')

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen(u'Logging in')

    #Methods for following #608
    def url_result(self, url, ie=None):
        """Returns a url that points to a page that should be processed"""
        #TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        return video_info
    def playlist_result(self, entries, playlist_id=None, playlist_title=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        return video_info

    def _search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        """
        Perform a regex search on the given string, using a single or a list of
        patterns returning the first matching group.
        In case of failure return a default value or raise a WARNING or a
        RegexNotFoundError, depending on fatal, specifying the field name.
        """
        if isinstance(pattern, (str, compat_str, compiled_regex_type)):
            mobj = re.search(pattern, string, flags)
        else:
            for p in pattern:
                mobj = re.search(p, string, flags)
                if mobj: break

        if sys.stderr.isatty() and os.name != 'nt':
            _name = u'\033[0;34m%s\033[0m' % name
        else:
            _name = name

        if mobj:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif default is not None:
            return default
        elif fatal:
            raise RegexNotFoundError(u'Unable to extract %s' % _name)
        else:
            self._downloader.report_warning(u'unable to extract %s; '
                u'please report this issue on http://yt-dl.org/bug' % _name)
            return None

    def _html_search_regex(self, pattern, string, name, default=None, fatal=True, flags=0):
        """
        Like _search_regex, but strips HTML tags and unescapes entities.
        """
        res = self._search_regex(pattern, string, name, default, fatal, flags)
        if res:
            return clean_html(res).strip()
        else:
            return res

    def _get_login_info(self):
        """
        Get the the login info as (username, password)
        It will look in the netrc file using the _NETRC_MACHINE value
        If there's no info available, return (None, None)
        """
        if self._downloader is None:
            return (None, None)

        username = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username', None) is not None:
            username = downloader_params['username']
            password = downloader_params['password']
        elif downloader_params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(self._NETRC_MACHINE)
                if info is not None:
                    username = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError('No authenticators for %s' % self._NETRC_MACHINE)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(u'parsing .netrc: %s' % compat_str(err))
        
        return (username, password)

    # Helper functions for extracting OpenGraph info
    @staticmethod
    def _og_regex(prop):
        return r'<meta.+?property=[\'"]og:%s[\'"].+?content=(?:"(.+?)"|\'(.+?)\')' % re.escape(prop)

    def _og_search_property(self, prop, html, name=None, **kargs):
        if name is None:
            name = 'OpenGraph %s' % prop
        escaped = self._search_regex(self._og_regex(prop), html, name, flags=re.DOTALL, **kargs)
        if not escaped is None:
            return unescapeHTML(escaped)
        return None

    def _og_search_thumbnail(self, html, **kargs):
        return self._og_search_property('image', html, u'thumbnail url', fatal=False, **kargs)

    def _og_search_description(self, html, **kargs):
        return self._og_search_property('description', html, fatal=False, **kargs)

    def _og_search_title(self, html, **kargs):
        return self._og_search_property('title', html, **kargs)

    def _og_search_video_url(self, html, name='video url', secure=True, **kargs):
        regexes = [self._og_regex('video')]
        if secure: regexes.insert(0, self._og_regex('video:secure_url'))
        return self._html_search_regex(regexes, html, name, **kargs)

    def _rta_search(self, html):
        # See http://www.rtalabel.org/index.php?content=howtofaq#single
        if re.search(r'(?ix)<meta\s+name="rating"\s+'
                     r'     content="RTA-5042-1996-1400-1577-RTA"',
                     html):
            return 18
        return 0


class SearchInfoExtractor(InfoExtractor):
    """
    Base class for paged search queries extractors.
    They accept urls in the format _SEARCH_KEY(|all|[0-9]):{query}
    Instances should define _SEARCH_KEY and _MAX_RESULTS.
    """

    @classmethod
    def _make_valid_url(cls):
        return r'%s(?P<prefix>|[1-9][0-9]*|all):(?P<query>[\s\S]+)' % cls._SEARCH_KEY

    @classmethod
    def suitable(cls, url):
        return re.match(cls._make_valid_url(), url) is not None

    def _real_extract(self, query):
        mobj = re.match(self._make_valid_url(), query)
        if mobj is None:
            raise ExtractorError(u'Invalid search query "%s"' % query)

        prefix = mobj.group('prefix')
        query = mobj.group('query')
        if prefix == '':
            return self._get_n_results(query, 1)
        elif prefix == 'all':
            return self._get_n_results(query, self._MAX_RESULTS)
        else:
            n = int(prefix)
            if n <= 0:
                raise ExtractorError(u'invalid download number %s for query "%s"' % (n, query))
            elif n > self._MAX_RESULTS:
                self._downloader.report_warning(u'%s returns max %i results (you requested %i)' % (self._SEARCH_KEY, self._MAX_RESULTS, n))
                n = self._MAX_RESULTS
            return self._get_n_results(query, n)

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        raise NotImplementedError("This method must be implemented by subclasses")

    @property
    def SEARCH_KEY(self):
        return self._SEARCH_KEY
