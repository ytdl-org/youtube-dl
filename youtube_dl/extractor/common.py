import base64
import hashlib
import json
import os
import re
import socket
import sys
import netrc
import xml.etree.ElementTree

from ..utils import (
    compat_http_client,
    compat_urllib_error,
    compat_urllib_parse_urlparse,
    compat_str,

    clean_html,
    compiled_regex_type,
    ExtractorError,
    RegexNotFoundError,
    sanitize_filename,
    unescapeHTML,
)
_NO_DEFAULT = object()


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
    title:          Video title, unescaped.

    Additionally, it must contain either a formats entry or a url one:

    formats:        A list of dictionaries for each format available, ordered
                    from worst to best quality.

                    Potential fields:
                    * url        Mandatory. The URL of the video file
                    * ext        Will be calculated from url if missing
                    * format     A human-readable description of the format
                                 ("mp4 container with h264/opus").
                                 Calculated from the format_id, width, height.
                                 and format_note fields if missing.
                    * format_id  A short description of the format
                                 ("mp4_h264_opus" or "19").
                                Technically optional, but strongly recommended.
                    * format_note Additional info about the format
                                 ("3D" or "DASH video")
                    * width      Width of the video, if known
                    * height     Height of the video, if known
                    * resolution Textual description of width and height
                    * tbr        Average bitrate of audio and video in KBit/s
                    * abr        Average audio bitrate in KBit/s
                    * acodec     Name of the audio codec in use
                    * asr        Audio sampling rate in Hertz
                    * vbr        Average video bitrate in KBit/s
                    * vcodec     Name of the video codec in use
                    * container  Name of the container format
                    * filesize   The number of bytes, if known in advance
                    * player_url SWF Player URL (used for rtmpdump).
                    * protocol   The protocol that will be used for the actual
                                 download, lower-case.
                                 "http", "https", "rtsp", "rtmp", "m3u8" or so.
                    * preference Order number of this format. If this field is
                                 present and not None, the formats get sorted
                                 by this field.
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
                    * quality    Order number of the video quality of this
                                 format, irrespective of the file format.
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
    url:            Final video URL.
    ext:            Video filename extension.
    format:         The video format, defaults to ext (used for --get-format)
    player_url:     SWF Player URL (used for rtmpdump).

    The following fields are optional:

    display_id      An alternative identifier for the video, not necessarily
                    unique, but available before title. Typically, id is
                    something like "4234987", title "Dancing naked mole rats",
                    and display_id "dancing-naked-mole-rats"
    thumbnails:     A list of dictionaries (with the entries "resolution" and
                    "url") for the varying thumbnails
    thumbnail:      Full URL to a video thumbnail image.
    description:    One-line video description.
    uploader:       Full name of the video uploader.
    timestamp:      UNIX timestamp of the moment the video became available.
    upload_date:    Video upload date (YYYYMMDD).
                    If not explicitly set, calculated from timestamp.
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location of the video.
    subtitles:      The subtitle file contents as a dictionary in the format
                    {language: subtitles}.
    duration:       Length of the video in seconds, as an integer.
    view_count:     How many users have watched the video on the platform.
    like_count:     Number of positive ratings of the video
    dislike_count:  Number of negative ratings of the video
    comment_count:  Number of comments on the video
    age_limit:      Age restriction for the video, as an integer (years)
    webpage_url:    The url to the video webpage, if given to youtube-dl it
                    should allow to get the same result again. (It will be set
                    by YoutubeDL if it's missing)

    Unless mentioned otherwise, the fields should be Unicode strings.

    Subclasses of this one should re-define the _real_initialize() and
    _real_extract() methods and define a _VALID_URL regexp.
    Probably, they should also be added to the list of extractors.

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

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen(u'%s' % (note,))
            else:
                self.to_screen(u'%s: %s' % (video_id, note))
        try:
            return self._downloader.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is False:
                return False
            if errnote is None:
                errnote = u'Unable to download webpage'
            errmsg = u'%s: %s' % (errnote, compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self._downloader.report_warning(errmsg)
                return False

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None, fatal=True):
        """ Returns a tuple (page content as string, URL handle) """

        # Strip hashes from the URL (#1038)
        if isinstance(url_or_request, (compat_str, str)):
            url_or_request = url_or_request.partition('#')[0]

        urlh = self._request_webpage(url_or_request, video_id, note, errnote, fatal)
        if urlh is False:
            assert not fatal
            return False
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
            elif webpage_bytes.startswith(b'\xff\xfe'):
                encoding = 'utf-16'
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
            if len(url) > 200:
                h = u'___' + hashlib.md5(url.encode('utf-8')).hexdigest()
                url = url[:200 - len(h)] + h
            raw_filename = ('%s_%s.dump' % (video_id, url))
            filename = sanitize_filename(raw_filename, restricted=True)
            self.to_screen(u'Saving request to ' + filename)
            with open(filename, 'wb') as outf:
                outf.write(webpage_bytes)

        content = webpage_bytes.decode(encoding, 'replace')
        return (content, urlh)

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True):
        """ Returns the data of the page as a string """
        res = self._download_webpage_handle(url_or_request, video_id, note, errnote, fatal)
        if res is False:
            return res
        else:
            content, _ = res
            return content

    def _download_xml(self, url_or_request, video_id,
                      note=u'Downloading XML', errnote=u'Unable to download XML',
                      transform_source=None):
        """Return the xml as an xml.etree.ElementTree.Element"""
        xml_string = self._download_webpage(url_or_request, video_id, note, errnote)
        if transform_source:
            xml_string = transform_source(xml_string)
        return xml.etree.ElementTree.fromstring(xml_string.encode('utf-8'))

    def _download_json(self, url_or_request, video_id,
                       note=u'Downloading JSON metadata',
                       errnote=u'Unable to download JSON metadata',
                       transform_source=None):
        json_string = self._download_webpage(url_or_request, video_id, note, errnote)
        if transform_source:
            json_string = transform_source(json_string)
        try:
            return json.loads(json_string)
        except ValueError as ve:
            raise ExtractorError('Failed to download JSON', cause=ve)

    def report_warning(self, msg, video_id=None):
        idstr = u'' if video_id is None else u'%s: ' % video_id
        self._downloader.report_warning(
            u'[%s] %s%s' % (self.IE_NAME, idstr, msg))

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
    @staticmethod
    def url_result(url, ie=None, video_id=None):
        """Returns a url that points to a page that should be processed"""
        #TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        if video_id is not None:
            video_info['id'] = video_id
        return video_info
    @staticmethod
    def playlist_result(entries, playlist_id=None, playlist_title=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        return video_info

    def _search_regex(self, pattern, string, name, default=_NO_DEFAULT, fatal=True, flags=0):
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

        if os.name != 'nt' and sys.stderr.isatty():
            _name = u'\033[0;34m%s\033[0m' % name
        else:
            _name = name

        if mobj:
            # return the first matching group
            return next(g for g in mobj.groups() if g is not None)
        elif default is not _NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError(u'Unable to extract %s' % _name)
        else:
            self._downloader.report_warning(u'unable to extract %s; '
                u'please report this issue on http://yt-dl.org/bug' % _name)
            return None

    def _html_search_regex(self, pattern, string, name, default=_NO_DEFAULT, fatal=True, flags=0):
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
    def _og_regexes(prop):
        content_re = r'content=(?:"([^>]+?)"|\'([^>]+?)\')'
        property_re = r'(?:name|property)=[\'"]og:%s[\'"]' % re.escape(prop)
        template = r'<meta[^>]+?%s[^>]+?%s'
        return [
            template % (property_re, content_re),
            template % (content_re, property_re),
        ]

    def _og_search_property(self, prop, html, name=None, **kargs):
        if name is None:
            name = 'OpenGraph %s' % prop
        escaped = self._search_regex(self._og_regexes(prop), html, name, flags=re.DOTALL, **kargs)
        if escaped is None:
            return None
        return unescapeHTML(escaped)

    def _og_search_thumbnail(self, html, **kargs):
        return self._og_search_property('image', html, u'thumbnail url', fatal=False, **kargs)

    def _og_search_description(self, html, **kargs):
        return self._og_search_property('description', html, fatal=False, **kargs)

    def _og_search_title(self, html, **kargs):
        return self._og_search_property('title', html, **kargs)

    def _og_search_video_url(self, html, name='video url', secure=True, **kargs):
        regexes = self._og_regexes('video')
        if secure: regexes = self._og_regexes('video:secure_url') + regexes
        return self._html_search_regex(regexes, html, name, **kargs)

    def _html_search_meta(self, name, html, display_name=None, fatal=False):
        if display_name is None:
            display_name = name
        return self._html_search_regex(
            r'''(?ix)<meta
                    (?=[^>]+(?:itemprop|name|property)=["\']%s["\'])
                    [^>]+content=["\']([^"\']+)["\']''' % re.escape(name),
            html, display_name, fatal=fatal)

    def _dc_search_uploader(self, html):
        return self._html_search_meta('dc.creator', html, 'uploader')

    def _rta_search(self, html):
        # See http://www.rtalabel.org/index.php?content=howtofaq#single
        if re.search(r'(?ix)<meta\s+name="rating"\s+'
                     r'     content="RTA-5042-1996-1400-1577-RTA"',
                     html):
            return 18
        return 0

    def _media_rating_search(self, html):
        # See http://www.tjg-designs.com/WP/metadata-code-examples-adding-metadata-to-your-web-pages/
        rating = self._html_search_meta('rating', html)

        if not rating:
            return None

        RATING_TABLE = {
            'safe for kids': 0,
            'general': 8,
            '14 years': 14,
            'mature': 17,
            'restricted': 19,
        }
        return RATING_TABLE.get(rating.lower(), None)

    def _twitter_search_player(self, html):
        return self._html_search_meta('twitter:player', html,
            'twitter card player')

    def _sort_formats(self, formats):
        if not formats:
            raise ExtractorError(u'No video formats found')

        def _formats_key(f):
            # TODO remove the following workaround
            from ..utils import determine_ext
            if not f.get('ext') and 'url' in f:
                f['ext'] = determine_ext(f['url'])

            preference = f.get('preference')
            if preference is None:
                proto = f.get('protocol')
                if proto is None:
                    proto = compat_urllib_parse_urlparse(f.get('url', '')).scheme

                preference = 0 if proto in ['http', 'https'] else -0.1
                if f.get('ext') in ['f4f', 'f4m']:  # Not yet supported
                    preference -= 0.5

            if f.get('vcodec') == 'none':  # audio only
                if self._downloader.params.get('prefer_free_formats'):
                    ORDER = [u'aac', u'mp3', u'm4a', u'webm', u'ogg', u'opus']
                else:
                    ORDER = [u'webm', u'opus', u'ogg', u'mp3', u'aac', u'm4a']
                ext_preference = 0
                try:
                    audio_ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    audio_ext_preference = -1
            else:
                if self._downloader.params.get('prefer_free_formats'):
                    ORDER = [u'flv', u'mp4', u'webm']
                else:
                    ORDER = [u'webm', u'flv', u'mp4']
                try:
                    ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    ext_preference = -1
                audio_ext_preference = 0

            return (
                preference,
                f.get('quality') if f.get('quality') is not None else -1,
                f.get('height') if f.get('height') is not None else -1,
                f.get('width') if f.get('width') is not None else -1,
                ext_preference,
                f.get('tbr') if f.get('tbr') is not None else -1,
                f.get('vbr') if f.get('vbr') is not None else -1,
                f.get('abr') if f.get('abr') is not None else -1,
                audio_ext_preference,
                f.get('filesize') if f.get('filesize') is not None else -1,
                f.get('format_id'),
            )
        formats.sort(key=_formats_key)


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
