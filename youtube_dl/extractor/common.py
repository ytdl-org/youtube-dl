from __future__ import unicode_literals

import base64
import datetime
import hashlib
import json
import netrc
import os
import re
import socket
import sys
import time
import xml.etree.ElementTree

from ..compat import (
    compat_cookiejar,
    compat_HTTPError,
    compat_http_client,
    compat_urllib_error,
    compat_urllib_parse_urlparse,
    compat_urlparse,
    compat_str,
)
from ..utils import (
    age_restricted,
    clean_html,
    compiled_regex_type,
    ExtractorError,
    float_or_none,
    HEADRequest,
    int_or_none,
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
    passed to the YoutubeDL. The YoutubeDL processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The type field determines the the type of the result.
    By far the most common value (and the default if _type is missing) is
    "video", which indicates a single video.

    For a video, the dictionaries must include the following fields:

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
                    * fps        Frame rate
                    * vcodec     Name of the video codec in use
                    * container  Name of the container format
                    * filesize   The number of bytes, if known in advance
                    * filesize_approx  An estimate for the number of bytes
                    * player_url SWF Player URL (used for rtmpdump).
                    * protocol   The protocol that will be used for the actual
                                 download, lower-case.
                                 "http", "https", "rtsp", "rtmp", "rtmpe",
                                 "m3u8", or "m3u8_native".
                    * preference Order number of this format. If this field is
                                 present and not None, the formats get sorted
                                 by this field, regardless of all other values.
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
                                 < -1000 to hide the format (if there is
                                    another one which is strictly better)
                    * language_preference  Is this in the correct requested
                                 language?
                                 10 if it's what the URL is about,
                                 -1 for default (don't know),
                                 -10 otherwise, other values reserved for now.
                    * quality    Order number of the video quality of this
                                 format, irrespective of the file format.
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
                    * source_preference  Order number for this video source
                                  (quality takes higher priority)
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
                    * http_method  HTTP method to use for the download.
                    * http_headers  A dictionary of additional HTTP headers
                                 to add to the request.
                    * http_post_data  Additional data to send with a POST
                                 request.
                    * stretched_ratio  If given and not 1, indicates that the
                                 video's pixels are not square.
                                 width : height ratio as float.
                    * no_resume  The server does not support resuming the
                                 (HTTP or RTMP) download. Boolean.

    url:            Final video URL.
    ext:            Video filename extension.
    format:         The video format, defaults to ext (used for --get-format)
    player_url:     SWF Player URL (used for rtmpdump).

    The following fields are optional:

    alt_title:      A secondary title of the video.
    display_id      An alternative identifier for the video, not necessarily
                    unique, but available before title. Typically, id is
                    something like "4234987", title "Dancing naked mole rats",
                    and display_id "dancing-naked-mole-rats"
    thumbnails:     A list of dictionaries, with the following entries:
                        * "id" (optional, string) - Thumbnail format ID
                        * "url"
                        * "preference" (optional, int) - quality of the image
                        * "width" (optional, int)
                        * "height" (optional, int)
                        * "resolution" (optional, string "{width}x{height"},
                                        deprecated)
    thumbnail:      Full URL to a video thumbnail image.
    description:    Full video description.
    uploader:       Full name of the video uploader.
    creator:        The main artist who created the video.
    timestamp:      UNIX timestamp of the moment the video became available.
    upload_date:    Video upload date (YYYYMMDD).
                    If not explicitly set, calculated from timestamp.
    uploader_id:    Nickname or id of the video uploader.
    location:       Physical location where the video was filmed.
    subtitles:      The subtitle file contents as a dictionary in the format
                    {language: subtitles}.
    duration:       Length of the video in seconds, as an integer.
    view_count:     How many users have watched the video on the platform.
    like_count:     Number of positive ratings of the video
    dislike_count:  Number of negative ratings of the video
    average_rating: Average rating give by users, the scale used depends on the webpage
    comment_count:  Number of comments on the video
    comments:       A list of comments, each with one or more of the following
                    properties (all but one of text or html optional):
                        * "author" - human-readable name of the comment author
                        * "author_id" - user ID of the comment author
                        * "id" - Comment ID
                        * "html" - Comment as HTML
                        * "text" - Plain text of the comment
                        * "timestamp" - UNIX timestamp of comment
                        * "parent" - ID of the comment this one is replying to.
                                     Set to "root" to indicate that this is a
                                     comment to the original video.
    age_limit:      Age restriction for the video, as an integer (years)
    webpage_url:    The url to the video webpage, if given to youtube-dl it
                    should allow to get the same result again. (It will be set
                    by YoutubeDL if it's missing)
    categories:     A list of categories that the video falls in, for example
                    ["Sports", "Berlin"]
    is_live:        True, False, or None (=unknown). Whether this video is a
                    live stream that goes on instead of a fixed-length video.

    Unless mentioned otherwise, the fields should be Unicode strings.

    Unless mentioned otherwise, None is equivalent to absence of information.


    _type "playlist" indicates multiple videos.
    There must be a key "entries", which is a list, an iterable, or a PagedList
    object, each element of which is a valid dictionary by this specification.

    Additionally, playlists can have "title" and "id" attributes with the same
    semantics as videos (see above).


    _type "multi_video" indicates that there are multiple videos that
    form a single show, for examples multiple acts of an opera or TV episode.
    It must have an entries key like a playlist and contain all the keys
    required for a video at the same time.


    _type "url" indicates that the video must be extracted from another
    location, possibly by a different extractor. Its only required key is:
    "url" - the next URL to extract.
    The key "ie_key" can be set to the class name (minus the trailing "IE",
    e.g. "Youtube") if the extractor class is known in advance.
    Additionally, the dictionary may have any properties of the resolved entity
    known in advance, for example "title" if the title of the referred video is
    known ahead of time.


    _type "url_transparent" entities have the same specification as "url", but
    indicate that the given additional information is more precise than the one
    associated with the resolved URL.
    This is useful when a site employs a video service that hosts the video and
    its technical metadata, but that video service does not embed a useful
    title, description etc.


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
    def _match_id(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        m = cls._VALID_URL_RE.match(url)
        assert m
        return m.group('id')

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
        try:
            self.initialize()
            return self._real_extract(url)
        except ExtractorError:
            raise
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occured.', cause=e, expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occured.', cause=e)

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
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))
        try:
            return self._downloader.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'
            errmsg = '%s: %s' % (errnote, compat_str(err))
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
        content = self._webpage_read_content(urlh, url_or_request, video_id, note, errnote, fatal)
        return (content, urlh)

    def _webpage_read_content(self, urlh, url_or_request, video_id, note=None, errnote=None, fatal=True, prefix=None):
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        if prefix is not None:
            webpage_bytes = prefix + webpage_bytes
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
            self.to_screen('Dumping request to ' + url)
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self._downloader.to_screen(dump)
        if self._downloader.params.get('write_pages', False):
            try:
                url = url_or_request.get_full_url()
            except AttributeError:
                url = url_or_request
            basen = '%s_%s' % (video_id, url)
            if len(basen) > 240:
                h = '___' + hashlib.md5(basen.encode('utf-8')).hexdigest()
                basen = basen[:240 - len(h)] + h
            raw_filename = basen + '.dump'
            filename = sanitize_filename(raw_filename, restricted=True)
            self.to_screen('Saving request to ' + filename)
            # Working around MAX_PATH limitation on Windows (see
            # http://msdn.microsoft.com/en-us/library/windows/desktop/aa365247(v=vs.85).aspx)
            if os.name == 'nt':
                absfilepath = os.path.abspath(filename)
                if len(absfilepath) > 259:
                    filename = '\\\\?\\' + absfilepath
            with open(filename, 'wb') as outf:
                outf.write(webpage_bytes)

        try:
            content = webpage_bytes.decode(encoding, 'replace')
        except LookupError:
            content = webpage_bytes.decode('utf-8', 'replace')

        if ('<title>Access to this site is blocked</title>' in content and
                'Websense' in content[:512]):
            msg = 'Access to this webpage has been blocked by Websense filtering software in your network.'
            blocked_iframe = self._html_search_regex(
                r'<iframe src="([^"]+)"', content,
                'Websense information URL', default=None)
            if blocked_iframe:
                msg += ' Visit %s for more details' % blocked_iframe
            raise ExtractorError(msg, expected=True)

        return content

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, tries=1, timeout=5):
        """ Returns the data of the page as a string """
        success = False
        try_count = 0
        while success is False:
            try:
                res = self._download_webpage_handle(url_or_request, video_id, note, errnote, fatal)
                success = True
            except compat_http_client.IncompleteRead as e:
                try_count += 1
                if try_count >= tries:
                    raise e
                self._sleep(timeout, video_id)
        if res is False:
            return res
        else:
            content, _ = res
            return content

    def _download_xml(self, url_or_request, video_id,
                      note='Downloading XML', errnote='Unable to download XML',
                      transform_source=None, fatal=True):
        """Return the xml as an xml.etree.ElementTree.Element"""
        xml_string = self._download_webpage(
            url_or_request, video_id, note, errnote, fatal=fatal)
        if xml_string is False:
            return xml_string
        if transform_source:
            xml_string = transform_source(xml_string)
        return xml.etree.ElementTree.fromstring(xml_string.encode('utf-8'))

    def _download_json(self, url_or_request, video_id,
                       note='Downloading JSON metadata',
                       errnote='Unable to download JSON metadata',
                       transform_source=None,
                       fatal=True):
        json_string = self._download_webpage(
            url_or_request, video_id, note, errnote, fatal=fatal)
        if (not fatal) and json_string is False:
            return None
        return self._parse_json(
            json_string, video_id, transform_source=transform_source, fatal=fatal)

    def _parse_json(self, json_string, video_id, transform_source=None, fatal=True):
        if transform_source:
            json_string = transform_source(json_string)
        try:
            return json.loads(json_string)
        except ValueError as ve:
            errmsg = '%s: Failed to parse JSON ' % video_id
            if fatal:
                raise ExtractorError(errmsg, cause=ve)
            else:
                self.report_warning(errmsg + str(ve))

    def report_warning(self, msg, video_id=None):
        idstr = '' if video_id is None else '%s: ' % video_id
        self._downloader.report_warning(
            '[%s] %s%s' % (self.IE_NAME, idstr, msg))

    def to_screen(self, msg):
        """Print msg to screen, prefixing it with '[ie_name]'"""
        self._downloader.to_screen('[%s] %s' % (self.IE_NAME, msg))

    def report_extraction(self, id_or_name):
        """Report information extraction."""
        self.to_screen('%s: Extracting information' % id_or_name)

    def report_download_webpage(self, video_id):
        """Report webpage download."""
        self.to_screen('%s: Downloading webpage' % video_id)

    def report_age_confirmation(self):
        """Report attempt to confirm age."""
        self.to_screen('Confirming age')

    def report_login(self):
        """Report attempt to log in."""
        self.to_screen('Logging in')

    # Methods for following #608
    @staticmethod
    def url_result(url, ie=None, video_id=None):
        """Returns a url that points to a page that should be processed"""
        # TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        if video_id is not None:
            video_info['id'] = video_id
        return video_info

    @staticmethod
    def playlist_result(entries, playlist_id=None, playlist_title=None, playlist_description=None):
        """Returns a playlist"""
        video_info = {'_type': 'playlist',
                      'entries': entries}
        if playlist_id:
            video_info['id'] = playlist_id
        if playlist_title:
            video_info['title'] = playlist_title
        if playlist_description:
            video_info['description'] = playlist_description
        return video_info

    def _search_regex(self, pattern, string, name, default=_NO_DEFAULT, fatal=True, flags=0, group=None):
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
                if mobj:
                    break

        if not self._downloader.params.get('no_color') and os.name != 'nt' and sys.stderr.isatty():
            _name = '\033[0;34m%s\033[0m' % name
        else:
            _name = name

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            else:
                return mobj.group(group)
        elif default is not _NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract %s' % _name)
        else:
            self._downloader.report_warning('unable to extract %s; '
                                            'please report this issue on http://yt-dl.org/bug' % _name)
            return None

    def _html_search_regex(self, pattern, string, name, default=_NO_DEFAULT, fatal=True, flags=0, group=None):
        """
        Like _search_regex, but strips HTML tags and unescapes entities.
        """
        res = self._search_regex(pattern, string, name, default, fatal, flags, group)
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
                self._downloader.report_warning('parsing .netrc: %s' % compat_str(err))

        return (username, password)

    def _get_tfa_info(self):
        """
        Get the two-factor authentication info
        TODO - asking the user will be required for sms/phone verify
        currently just uses the command line option
        If there's no info available, return None
        """
        if self._downloader is None:
            return None
        downloader_params = self._downloader.params

        if downloader_params.get('twofactor', None) is not None:
            return downloader_params['twofactor']

        return None

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
        return self._og_search_property('image', html, 'thumbnail url', fatal=False, **kargs)

    def _og_search_description(self, html, **kargs):
        return self._og_search_property('description', html, fatal=False, **kargs)

    def _og_search_title(self, html, **kargs):
        return self._og_search_property('title', html, **kargs)

    def _og_search_video_url(self, html, name='video url', secure=True, **kargs):
        regexes = self._og_regexes('video') + self._og_regexes('video:url')
        if secure:
            regexes = self._og_regexes('video:secure_url') + regexes
        return self._html_search_regex(regexes, html, name, **kargs)

    def _og_search_url(self, html, **kargs):
        return self._og_search_property('url', html, **kargs)

    def _html_search_meta(self, name, html, display_name=None, fatal=False, **kwargs):
        if display_name is None:
            display_name = name
        return self._html_search_regex(
            r'''(?isx)<meta
                    (?=[^>]+(?:itemprop|name|property)=(["\']?)%s\1)
                    [^>]+?content=(["\'])(?P<content>.*?)\2''' % re.escape(name),
            html, display_name, fatal=fatal, group='content', **kwargs)

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

    def _family_friendly_search(self, html):
        # See http://schema.org/VideoObj
        family_friendly = self._html_search_meta('isFamilyFriendly', html)

        if not family_friendly:
            return None

        RATING_TABLE = {
            '1': 0,
            'true': 0,
            '0': 18,
            'false': 18,
        }
        return RATING_TABLE.get(family_friendly.lower(), None)

    def _twitter_search_player(self, html):
        return self._html_search_meta('twitter:player', html,
                                      'twitter card player')

    def _sort_formats(self, formats):
        if not formats:
            raise ExtractorError('No video formats found')

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
                    ORDER = ['aac', 'mp3', 'm4a', 'webm', 'ogg', 'opus']
                else:
                    ORDER = ['webm', 'opus', 'ogg', 'mp3', 'aac', 'm4a']
                ext_preference = 0
                try:
                    audio_ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    audio_ext_preference = -1
            else:
                if self._downloader.params.get('prefer_free_formats'):
                    ORDER = ['flv', 'mp4', 'webm']
                else:
                    ORDER = ['webm', 'flv', 'mp4']
                try:
                    ext_preference = ORDER.index(f['ext'])
                except ValueError:
                    ext_preference = -1
                audio_ext_preference = 0

            return (
                preference,
                f.get('language_preference') if f.get('language_preference') is not None else -1,
                f.get('quality') if f.get('quality') is not None else -1,
                f.get('tbr') if f.get('tbr') is not None else -1,
                f.get('vbr') if f.get('vbr') is not None else -1,
                f.get('height') if f.get('height') is not None else -1,
                f.get('width') if f.get('width') is not None else -1,
                ext_preference,
                f.get('abr') if f.get('abr') is not None else -1,
                audio_ext_preference,
                f.get('fps') if f.get('fps') is not None else -1,
                f.get('filesize') if f.get('filesize') is not None else -1,
                f.get('filesize_approx') if f.get('filesize_approx') is not None else -1,
                f.get('source_preference') if f.get('source_preference') is not None else -1,
                f.get('format_id'),
            )
        formats.sort(key=_formats_key)

    def _check_formats(self, formats, video_id):
        if formats:
            formats[:] = filter(
                lambda f: self._is_valid_url(
                    f['url'], video_id,
                    item='%s video format' % f.get('format_id') if f.get('format_id') else 'video'),
                formats)

    def _is_valid_url(self, url, video_id, item='video'):
        try:
            self._request_webpage(
                HEADRequest(url), video_id,
                'Checking %s URL' % item)
            return True
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError):
                self.report_warning(
                    '%s URL is invalid, skipping' % item, video_id)
                return False
            raise

    def http_scheme(self):
        """ Either "http:" or "https:", depending on the user's preferences """
        return (
            'http:'
            if self._downloader.params.get('prefer_insecure', False)
            else 'https:')

    def _proto_relative_url(self, url, scheme=None):
        if url is None:
            return url
        if url.startswith('//'):
            if scheme is None:
                scheme = self.http_scheme()
            return scheme + url
        else:
            return url

    def _sleep(self, timeout, video_id, msg_template=None):
        if msg_template is None:
            msg_template = '%(video_id)s: Waiting for %(timeout)s seconds'
        msg = msg_template % {'video_id': video_id, 'timeout': timeout}
        self.to_screen(msg)
        time.sleep(timeout)

    def _extract_f4m_formats(self, manifest_url, video_id, preference=None, f4m_id=None):
        manifest = self._download_xml(
            manifest_url, video_id, 'Downloading f4m manifest',
            'Unable to download f4m manifest')

        formats = []
        manifest_version = '1.0'
        media_nodes = manifest.findall('{http://ns.adobe.com/f4m/1.0}media')
        if not media_nodes:
            manifest_version = '2.0'
            media_nodes = manifest.findall('{http://ns.adobe.com/f4m/2.0}media')
        for i, media_el in enumerate(media_nodes):
            if manifest_version == '2.0':
                manifest_url = ('/'.join(manifest_url.split('/')[:-1]) + '/'
                                + (media_el.attrib.get('href') or media_el.attrib.get('url')))
            tbr = int_or_none(media_el.attrib.get('bitrate'))
            formats.append({
                'format_id': '-'.join(filter(None, [f4m_id, 'f4m-%d' % (i if tbr is None else tbr)])),
                'url': manifest_url,
                'ext': 'flv',
                'tbr': tbr,
                'width': int_or_none(media_el.attrib.get('width')),
                'height': int_or_none(media_el.attrib.get('height')),
                'preference': preference,
            })
        self._sort_formats(formats)

        return formats

    def _extract_m3u8_formats(self, m3u8_url, video_id, ext=None,
                              entry_protocol='m3u8', preference=None,
                              m3u8_id=None):

        formats = [{
            'format_id': '-'.join(filter(None, [m3u8_id, 'm3u8-meta'])),
            'url': m3u8_url,
            'ext': ext,
            'protocol': 'm3u8',
            'preference': -1,
            'resolution': 'multiple',
            'format_note': 'Quality selection URL',
        }]

        format_url = lambda u: (
            u
            if re.match(r'^https?://', u)
            else compat_urlparse.urljoin(m3u8_url, u))

        m3u8_doc = self._download_webpage(
            m3u8_url, video_id,
            note='Downloading m3u8 information',
            errnote='Failed to download m3u8 information')
        last_info = None
        kv_rex = re.compile(
            r'(?P<key>[a-zA-Z_-]+)=(?P<val>"[^"]+"|[^",]+)(?:,|$)')
        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-STREAM-INF:'):
                last_info = {}
                for m in kv_rex.finditer(line):
                    v = m.group('val')
                    if v.startswith('"'):
                        v = v[1:-1]
                    last_info[m.group('key')] = v
            elif line.startswith('#') or not line.strip():
                continue
            else:
                if last_info is None:
                    formats.append({'url': format_url(line)})
                    continue
                tbr = int_or_none(last_info.get('BANDWIDTH'), scale=1000)
                f = {
                    'format_id': '-'.join(filter(None, [m3u8_id, 'm3u8-%d' % (tbr if tbr else len(formats))])),
                    'url': format_url(line.strip()),
                    'tbr': tbr,
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                codecs = last_info.get('CODECS')
                if codecs:
                    # TODO: looks like video codec is not always necessarily goes first
                    va_codecs = codecs.split(',')
                    if va_codecs[0]:
                        f['vcodec'] = va_codecs[0].partition('.')[0]
                    if len(va_codecs) > 1 and va_codecs[1]:
                        f['acodec'] = va_codecs[1].partition('.')[0]
                resolution = last_info.get('RESOLUTION')
                if resolution:
                    width_str, height_str = resolution.split('x')
                    f['width'] = int(width_str)
                    f['height'] = int(height_str)
                formats.append(f)
                last_info = {}
        self._sort_formats(formats)
        return formats

    # TODO: improve extraction
    def _extract_smil_formats(self, smil_url, video_id, fatal=True):
        smil = self._download_xml(
            smil_url, video_id, 'Downloading SMIL file',
            'Unable to download SMIL file', fatal=fatal)
        if smil is False:
            assert not fatal
            return []

        base = smil.find('./head/meta').get('base')

        formats = []
        rtmp_count = 0
        for video in smil.findall('./body/switch/video'):
            src = video.get('src')
            if not src:
                continue
            bitrate = int_or_none(video.get('system-bitrate') or video.get('systemBitrate'), 1000)
            width = int_or_none(video.get('width'))
            height = int_or_none(video.get('height'))
            proto = video.get('proto')
            if not proto:
                if base:
                    if base.startswith('rtmp'):
                        proto = 'rtmp'
                    elif base.startswith('http'):
                        proto = 'http'
            ext = video.get('ext')
            if proto == 'm3u8':
                formats.extend(self._extract_m3u8_formats(src, video_id, ext))
            elif proto == 'rtmp':
                rtmp_count += 1
                streamer = video.get('streamer') or base
                formats.append({
                    'url': streamer,
                    'play_path': src,
                    'ext': 'flv',
                    'format_id': 'rtmp-%d' % (rtmp_count if bitrate is None else bitrate),
                    'tbr': bitrate,
                    'width': width,
                    'height': height,
                })
        self._sort_formats(formats)

        return formats

    def _live_title(self, name):
        """ Generate the title for a live video """
        now = datetime.datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M")
        return name + ' ' + now_str

    def _int(self, v, name, fatal=False, **kwargs):
        res = int_or_none(v, **kwargs)
        if 'get_attr' in kwargs:
            print(getattr(v, kwargs['get_attr']))
        if res is None:
            msg = 'Failed to extract %s: Could not parse value %r' % (name, v)
            if fatal:
                raise ExtractorError(msg)
            else:
                self._downloader.report_warning(msg)
        return res

    def _float(self, v, name, fatal=False, **kwargs):
        res = float_or_none(v, **kwargs)
        if res is None:
            msg = 'Failed to extract %s: Could not parse value %r' % (name, v)
            if fatal:
                raise ExtractorError(msg)
            else:
                self._downloader.report_warning(msg)
        return res

    def _set_cookie(self, domain, name, value, expire_time=None):
        cookie = compat_cookiejar.Cookie(
            0, name, value, None, None, domain, None,
            None, '/', True, False, expire_time, '', None, None, None)
        self._downloader.cookiejar.set_cookie(cookie)

    def get_testcases(self, include_onlymatching=False):
        t = getattr(self, '_TEST', None)
        if t:
            assert not hasattr(self, '_TESTS'), \
                '%s has _TEST and _TESTS' % type(self).__name__
            tests = [t]
        else:
            tests = getattr(self, '_TESTS', [])
        for t in tests:
            if not include_onlymatching and t.get('only_matching', False):
                continue
            t['name'] = type(self).__name__[:-len('IE')]
            yield t

    def is_suitable(self, age_limit):
        """ Test whether the extractor is generally suitable for the given
        age limit (i.e. pornographic sites are not, all others usually are) """

        any_restricted = False
        for tc in self.get_testcases(include_onlymatching=False):
            if 'playlist' in tc:
                tc = tc['playlist'][0]
            is_restricted = age_restricted(
                tc.get('info_dict', {}).get('age_limit'), age_limit)
            if not is_restricted:
                return True
            any_restricted = any_restricted or is_restricted
        return not any_restricted


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
            raise ExtractorError('Invalid search query "%s"' % query)

        prefix = mobj.group('prefix')
        query = mobj.group('query')
        if prefix == '':
            return self._get_n_results(query, 1)
        elif prefix == 'all':
            return self._get_n_results(query, self._MAX_RESULTS)
        else:
            n = int(prefix)
            if n <= 0:
                raise ExtractorError('invalid download number %s for query "%s"' % (n, query))
            elif n > self._MAX_RESULTS:
                self._downloader.report_warning('%s returns max %i results (you requested %i)' % (self._SEARCH_KEY, self._MAX_RESULTS, n))
                n = self._MAX_RESULTS
            return self._get_n_results(query, n)

    def _get_n_results(self, query, n):
        """Get a specified number of results for a query"""
        raise NotImplementedError("This method must be implemented by subclasses")

    @property
    def SEARCH_KEY(self):
        return self._SEARCH_KEY
