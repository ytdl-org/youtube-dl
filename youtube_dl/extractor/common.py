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
import math

from ..compat import (
    compat_cookiejar,
    compat_cookies,
    compat_etree_fromstring,
    compat_getpass,
    compat_http_client,
    compat_os_name,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse_urlencode,
    compat_urllib_request,
    compat_urlparse,
)
from ..downloader.f4m import remove_encrypted_media
from ..utils import (
    NO_DEFAULT,
    age_restricted,
    bug_reports_message,
    clean_html,
    compiled_regex_type,
    determine_ext,
    error_to_compat_str,
    ExtractorError,
    fix_xml_ampersands,
    float_or_none,
    int_or_none,
    parse_iso8601,
    RegexNotFoundError,
    sanitize_filename,
    sanitized_Request,
    unescapeHTML,
    unified_strdate,
    url_basename,
    xpath_text,
    xpath_with_ns,
    determine_protocol,
    parse_duration,
    mimetype2ext,
    update_Request,
    update_url_query,
)


class InfoExtractor(object):
    """Information Extractor class.

    Information extractors are the classes that, given a URL, extract
    information about the video (or videos) the URL refers to. This
    information includes the real video URL, the video title, author and
    others. The information is stored in a dictionary which is then
    passed to the YoutubeDL. The YoutubeDL processes this
    information possibly downloading the video to the file system, among
    other possible outcomes.

    The type field determines the type of the result.
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
                    * ext        Will be calculated from URL if missing
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
                                 "m3u8", "m3u8_native" or "http_dash_segments".
                    * preference Order number of this format. If this field is
                                 present and not None, the formats get sorted
                                 by this field, regardless of all other values.
                                 -1 for default (order by other properties),
                                 -2 or smaller for less than default.
                                 < -1000 to hide the format (if there is
                                    another one which is strictly better)
                    * language   Language code, e.g. "de" or "en-US".
                    * language_preference  Is this in the language mentioned in
                                 the URL?
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
                    * http_headers  A dictionary of additional HTTP headers
                                 to add to the request.
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
    license:        License name the video is licensed under.
    creator:        The creator of the video.
    release_date:   The date (YYYYMMDD) when the video was released.
    timestamp:      UNIX timestamp of the moment the video became available.
    upload_date:    Video upload date (YYYYMMDD).
                    If not explicitly set, calculated from timestamp.
    uploader_id:    Nickname or id of the video uploader.
    uploader_url:   Full URL to a personal webpage of the video uploader.
    location:       Physical location where the video was filmed.
    subtitles:      The available subtitles as a dictionary in the format
                    {language: subformats}. "subformats" is a list sorted from
                    lower to higher preference, each element is a dictionary
                    with the "ext" entry and one of:
                        * "data": The subtitles file contents
                        * "url": A URL pointing to the subtitles file
                    "ext" will be calculated from URL if missing
    automatic_captions: Like 'subtitles', used by the YoutubeIE for
                    automatically generated captions
    duration:       Length of the video in seconds, as an integer or float.
    view_count:     How many users have watched the video on the platform.
    like_count:     Number of positive ratings of the video
    dislike_count:  Number of negative ratings of the video
    repost_count:   Number of reposts of the video
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
    webpage_url:    The URL to the video webpage, if given to youtube-dl it
                    should allow to get the same result again. (It will be set
                    by YoutubeDL if it's missing)
    categories:     A list of categories that the video falls in, for example
                    ["Sports", "Berlin"]
    tags:           A list of tags assigned to the video, e.g. ["sweden", "pop music"]
    is_live:        True, False, or None (=unknown). Whether this video is a
                    live stream that goes on instead of a fixed-length video.
    start_time:     Time in seconds where the reproduction should start, as
                    specified in the URL.
    end_time:       Time in seconds where the reproduction should end, as
                    specified in the URL.

    The following fields should only be used when the video belongs to some logical
    chapter or section:

    chapter:        Name or title of the chapter the video belongs to.
    chapter_number: Number of the chapter the video belongs to, as an integer.
    chapter_id:     Id of the chapter the video belongs to, as a unicode string.

    The following fields should only be used when the video is an episode of some
    series or programme:

    series:         Title of the series or programme the video episode belongs to.
    season:         Title of the season the video episode belongs to.
    season_number:  Number of the season the video episode belongs to, as an integer.
    season_id:      Id of the season the video episode belongs to, as a unicode string.
    episode:        Title of the video episode. Unlike mandatory video title field,
                    this field should denote the exact title of the video episode
                    without any kind of decoration.
    episode_number: Number of the video episode within a season, as an integer.
    episode_id:     Id of the video episode, as a unicode string.

    The following fields should only be used when the media is a track or a part of
    a music album:

    track:          Title of the track.
    track_number:   Number of the track within an album or a disc, as an integer.
    track_id:       Id of the track (useful in case of custom indexing, e.g. 6.iii),
                    as a unicode string.
    artist:         Artist(s) of the track.
    genre:          Genre(s) of the track.
    album:          Title of the album the track belongs to.
    album_type:     Type of the album (e.g. "Demo", "Full-length", "Split", "Compilation", etc).
    album_artist:   List of all artists appeared on the album (e.g.
                    "Ash Borer / Fell Voices" or "Various Artists", useful for splits
                    and compilations).
    disc_number:    Number of the disc or other physical medium the track belongs to,
                    as an integer.
    release_year:   Year (YYYY) when the album was released.

    Unless mentioned otherwise, the fields should be Unicode strings.

    Unless mentioned otherwise, None is equivalent to absence of information.


    _type "playlist" indicates multiple videos.
    There must be a key "entries", which is a list, an iterable, or a PagedList
    object, each element of which is a valid dictionary by this specification.

    Additionally, playlists can have "title", "description" and "id" attributes
    with the same semantics as videos (see above).


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
            raise ExtractorError('A network error has occurred.', cause=e, expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e)

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
        return compat_str(cls.__name__[:-2])

    @property
    def IE_NAME(self):
        return compat_str(type(self).__name__[:-2])

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}):
        """ Returns the response handle """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))
        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
            if data is not None or headers:
                url_or_request = sanitized_Request(url_or_request, data, headers)
        try:
            return self._downloader.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self._downloader.report_warning(errmsg)
                return False

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None, fatal=True, encoding=None, data=None, headers={}, query={}):
        """ Returns a tuple (page content as string, URL handle) """
        # Strip hashes from the URL (#1038)
        if isinstance(url_or_request, (compat_str, str)):
            url_or_request = url_or_request.partition('#')[0]

        urlh = self._request_webpage(url_or_request, video_id, note, errnote, fatal, data=data, headers=headers, query=query)
        if urlh is False:
            assert not fatal
            return False
        content = self._webpage_read_content(urlh, url_or_request, video_id, note, errnote, fatal, encoding=encoding)
        return (content, urlh)

    @staticmethod
    def _guess_encoding_from_content(content_type, webpage_bytes):
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

        return encoding

    def _webpage_read_content(self, urlh, url_or_request, video_id, note=None, errnote=None, fatal=True, prefix=None, encoding=None):
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        if prefix is not None:
            webpage_bytes = prefix + webpage_bytes
        if not encoding:
            encoding = self._guess_encoding_from_content(content_type, webpage_bytes)
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
            if compat_os_name == 'nt':
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
        if '<title>The URL you requested has been blocked</title>' in content[:512]:
            msg = (
                'Access to this webpage has been blocked by Indian censorship. '
                'Use a VPN or proxy server (with --proxy) to route around it.')
            block_msg = self._html_search_regex(
                r'</h1><p>(.*?)</p>',
                content, 'block message', default=None)
            if block_msg:
                msg += ' (Message: "%s")' % block_msg.replace('\n', ' ')
            raise ExtractorError(msg, expected=True)

        return content

    def _download_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, tries=1, timeout=5, encoding=None, data=None, headers={}, query={}):
        """ Returns the data of the page as a string """
        success = False
        try_count = 0
        while success is False:
            try:
                res = self._download_webpage_handle(url_or_request, video_id, note, errnote, fatal, encoding=encoding, data=data, headers=headers, query=query)
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
                      transform_source=None, fatal=True, encoding=None, data=None, headers={}, query={}):
        """Return the xml as an xml.etree.ElementTree.Element"""
        xml_string = self._download_webpage(
            url_or_request, video_id, note, errnote, fatal=fatal, encoding=encoding, data=data, headers=headers, query=query)
        if xml_string is False:
            return xml_string
        if transform_source:
            xml_string = transform_source(xml_string)
        return compat_etree_fromstring(xml_string.encode('utf-8'))

    def _download_json(self, url_or_request, video_id,
                       note='Downloading JSON metadata',
                       errnote='Unable to download JSON metadata',
                       transform_source=None,
                       fatal=True, encoding=None, data=None, headers={}, query={}):
        json_string = self._download_webpage(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query)
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

    @staticmethod
    def raise_login_required(msg='This video is only available for registered users'):
        raise ExtractorError(
            '%s. Use --username and --password or --netrc to provide account credentials.' % msg,
            expected=True)

    @staticmethod
    def raise_geo_restricted(msg='This video is not available from your location due to geo restriction'):
        raise ExtractorError(
            '%s. You might want to use --proxy to workaround.' % msg,
            expected=True)

    # Methods for following #608
    @staticmethod
    def url_result(url, ie=None, video_id=None, video_title=None):
        """Returns a URL that points to a page that should be processed"""
        # TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        if video_id is not None:
            video_info['id'] = video_id
        if video_title is not None:
            video_info['title'] = video_title
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

    def _search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
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

        if not self._downloader.params.get('no_color') and compat_os_name != 'nt' and sys.stderr.isatty():
            _name = '\033[0;34m%s\033[0m' % name
        else:
            _name = name

        if mobj:
            if group is None:
                # return the first matching group
                return next(g for g in mobj.groups() if g is not None)
            else:
                return mobj.group(group)
        elif default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract %s' % _name)
        else:
            self._downloader.report_warning('unable to extract %s' % _name + bug_reports_message())
            return None

    def _html_search_regex(self, pattern, string, name, default=NO_DEFAULT, fatal=True, flags=0, group=None):
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
        Get the login info as (username, password)
        It will look in the netrc file using the _NETRC_MACHINE value
        If there's no info available, return (None, None)
        """
        if self._downloader is None:
            return (None, None)

        username = None
        password = None
        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get('username') is not None:
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
                self._downloader.report_warning('parsing .netrc: %s' % error_to_compat_str(err))

        return (username, password)

    def _get_tfa_info(self, note='two-factor verification code'):
        """
        Get the two-factor authentication info
        TODO - asking the user will be required for sms/phone verify
        currently just uses the command line option
        If there's no info available, return None
        """
        if self._downloader is None:
            return None
        downloader_params = self._downloader.params

        if downloader_params.get('twofactor') is not None:
            return downloader_params['twofactor']

        return compat_getpass('Type %s and press [Return]: ' % note)

    # Helper functions for extracting OpenGraph info
    @staticmethod
    def _og_regexes(prop):
        content_re = r'content=(?:"([^"]+?)"|\'([^\']+?)\'|\s*([^\s"\'=<>`]+?))'
        property_re = (r'(?:name|property)=(?:\'og:%(prop)s\'|"og:%(prop)s"|\s*og:%(prop)s\b)'
                       % {'prop': re.escape(prop)})
        template = r'<meta[^>]+?%s[^>]+?%s'
        return [
            template % (property_re, content_re),
            template % (content_re, property_re),
        ]

    @staticmethod
    def _meta_regex(prop):
        return r'''(?isx)<meta
                    (?=[^>]+(?:itemprop|name|property|id|http-equiv)=(["\']?)%s\1)
                    [^>]+?content=(["\'])(?P<content>.*?)\2''' % re.escape(prop)

    def _og_search_property(self, prop, html, name=None, **kargs):
        if name is None:
            name = 'OpenGraph %s' % prop
        escaped = self._search_regex(self._og_regexes(prop), html, name, flags=re.DOTALL, **kargs)
        if escaped is None:
            return None
        return unescapeHTML(escaped)

    def _og_search_thumbnail(self, html, **kargs):
        return self._og_search_property('image', html, 'thumbnail URL', fatal=False, **kargs)

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
            self._meta_regex(name),
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
        return RATING_TABLE.get(rating.lower())

    def _family_friendly_search(self, html):
        # See http://schema.org/VideoObject
        family_friendly = self._html_search_meta('isFamilyFriendly', html)

        if not family_friendly:
            return None

        RATING_TABLE = {
            '1': 0,
            'true': 0,
            '0': 18,
            'false': 18,
        }
        return RATING_TABLE.get(family_friendly.lower())

    def _twitter_search_player(self, html):
        return self._html_search_meta('twitter:player', html,
                                      'twitter card player')

    def _search_json_ld(self, html, video_id, **kwargs):
        json_ld = self._search_regex(
            r'(?s)<script[^>]+type=(["\'])application/ld\+json\1[^>]*>(?P<json_ld>.+?)</script>',
            html, 'JSON-LD', group='json_ld', **kwargs)
        if not json_ld:
            return {}
        return self._json_ld(json_ld, video_id, fatal=kwargs.get('fatal', True))

    def _json_ld(self, json_ld, video_id, fatal=True):
        if isinstance(json_ld, compat_str):
            json_ld = self._parse_json(json_ld, video_id, fatal=fatal)
        if not json_ld:
            return {}
        info = {}
        if json_ld.get('@context') == 'http://schema.org':
            item_type = json_ld.get('@type')
            if item_type == 'TVEpisode':
                info.update({
                    'episode': unescapeHTML(json_ld.get('name')),
                    'episode_number': int_or_none(json_ld.get('episodeNumber')),
                    'description': unescapeHTML(json_ld.get('description')),
                })
                part_of_season = json_ld.get('partOfSeason')
                if isinstance(part_of_season, dict) and part_of_season.get('@type') == 'TVSeason':
                    info['season_number'] = int_or_none(part_of_season.get('seasonNumber'))
                part_of_series = json_ld.get('partOfSeries')
                if isinstance(part_of_series, dict) and part_of_series.get('@type') == 'TVSeries':
                    info['series'] = unescapeHTML(part_of_series.get('name'))
            elif item_type == 'Article':
                info.update({
                    'timestamp': parse_iso8601(json_ld.get('datePublished')),
                    'title': unescapeHTML(json_ld.get('headline')),
                    'description': unescapeHTML(json_ld.get('articleBody')),
                })
        return dict((k, v) for k, v in info.items() if v is not None)

    @staticmethod
    def _hidden_inputs(html):
        html = re.sub(r'<!--(?:(?!<!--).)*-->', '', html)
        hidden_inputs = {}
        for input in re.findall(r'(?i)<input([^>]+)>', html):
            if not re.search(r'type=(["\'])(?:hidden|submit)\1', input):
                continue
            name = re.search(r'(?:name|id)=(["\'])(?P<value>.+?)\1', input)
            if not name:
                continue
            value = re.search(r'value=(["\'])(?P<value>.*?)\1', input)
            if not value:
                continue
            hidden_inputs[name.group('value')] = value.group('value')
        return hidden_inputs

    def _form_hidden_inputs(self, form_id, html):
        form = self._search_regex(
            r'(?is)<form[^>]+?id=(["\'])%s\1[^>]*>(?P<form>.+?)</form>' % form_id,
            html, '%s form' % form_id, group='form')
        return self._hidden_inputs(form)

    def _sort_formats(self, formats, field_preference=None):
        if not formats:
            raise ExtractorError('No video formats found')

        for f in formats:
            # Automatically determine tbr when missing based on abr and vbr (improves
            # formats sorting in some cases)
            if 'tbr' not in f and f.get('abr') is not None and f.get('vbr') is not None:
                f['tbr'] = f['abr'] + f['vbr']

        def _formats_key(f):
            # TODO remove the following workaround
            from ..utils import determine_ext
            if not f.get('ext') and 'url' in f:
                f['ext'] = determine_ext(f['url'])

            if isinstance(field_preference, (list, tuple)):
                return tuple(f.get(field) if f.get(field) is not None else -1 for field in field_preference)

            preference = f.get('preference')
            if preference is None:
                preference = 0
                if f.get('ext') in ['f4f', 'f4m']:  # Not yet supported
                    preference -= 0.5

            proto_preference = 0 if determine_protocol(f) in ['http', 'https'] else -0.1

            if f.get('vcodec') == 'none':  # audio only
                preference -= 50
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
                if f.get('acodec') == 'none':  # video only
                    preference -= 40
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
                f.get('filesize') if f.get('filesize') is not None else -1,
                f.get('vbr') if f.get('vbr') is not None else -1,
                f.get('height') if f.get('height') is not None else -1,
                f.get('width') if f.get('width') is not None else -1,
                proto_preference,
                ext_preference,
                f.get('abr') if f.get('abr') is not None else -1,
                audio_ext_preference,
                f.get('fps') if f.get('fps') is not None else -1,
                f.get('filesize_approx') if f.get('filesize_approx') is not None else -1,
                f.get('source_preference') if f.get('source_preference') is not None else -1,
                f.get('format_id') if f.get('format_id') is not None else '',
            )
        formats.sort(key=_formats_key)

    def _check_formats(self, formats, video_id):
        if formats:
            formats[:] = filter(
                lambda f: self._is_valid_url(
                    f['url'], video_id,
                    item='%s video format' % f.get('format_id') if f.get('format_id') else 'video'),
                formats)

    @staticmethod
    def _remove_duplicate_formats(formats):
        format_urls = set()
        unique_formats = []
        for f in formats:
            if f['url'] not in format_urls:
                format_urls.add(f['url'])
                unique_formats.append(f)
        formats[:] = unique_formats

    def _is_valid_url(self, url, video_id, item='video'):
        url = self._proto_relative_url(url, scheme='http:')
        # For now assume non HTTP(S) URLs always valid
        if not (url.startswith('http://') or url.startswith('https://')):
            return True
        try:
            self._request_webpage(url, video_id, 'Checking %s URL' % item)
            return True
        except ExtractorError as e:
            if isinstance(e.cause, compat_urllib_error.URLError):
                self.to_screen(
                    '%s: %s URL is invalid, skipping' % (video_id, item))
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

    def _extract_f4m_formats(self, manifest_url, video_id, preference=None, f4m_id=None,
                             transform_source=lambda s: fix_xml_ampersands(s).strip(),
                             fatal=True):
        manifest = self._download_xml(
            manifest_url, video_id, 'Downloading f4m manifest',
            'Unable to download f4m manifest',
            # Some manifests may be malformed, e.g. prosiebensat1 generated manifests
            # (see https://github.com/rg3/youtube-dl/issues/6215#issuecomment-121704244)
            transform_source=transform_source,
            fatal=fatal)

        if manifest is False:
            return []

        return self._parse_f4m_formats(
            manifest, manifest_url, video_id, preference=preference, f4m_id=f4m_id,
            transform_source=transform_source, fatal=fatal)

    def _parse_f4m_formats(self, manifest, manifest_url, video_id, preference=None, f4m_id=None,
                           transform_source=lambda s: fix_xml_ampersands(s).strip(),
                           fatal=True):
        # currently youtube-dl cannot decode the playerVerificationChallenge as Akamai uses Adobe Alchemy
        akamai_pv = manifest.find('{http://ns.adobe.com/f4m/1.0}pv-2.0')
        if akamai_pv is not None and ';' in akamai_pv.text:
            playerVerificationChallenge = akamai_pv.text.split(';')[0]
            if playerVerificationChallenge.strip() != '':
                return []

        formats = []
        manifest_version = '1.0'
        media_nodes = manifest.findall('{http://ns.adobe.com/f4m/1.0}media')
        if not media_nodes:
            manifest_version = '2.0'
            media_nodes = manifest.findall('{http://ns.adobe.com/f4m/2.0}media')
        # Remove unsupported DRM protected media from final formats
        # rendition (see https://github.com/rg3/youtube-dl/issues/8573).
        media_nodes = remove_encrypted_media(media_nodes)
        if not media_nodes:
            return formats
        base_url = xpath_text(
            manifest, ['{http://ns.adobe.com/f4m/1.0}baseURL', '{http://ns.adobe.com/f4m/2.0}baseURL'],
            'base URL', default=None)
        if base_url:
            base_url = base_url.strip()
        for i, media_el in enumerate(media_nodes):
            if manifest_version == '2.0':
                media_url = media_el.attrib.get('href') or media_el.attrib.get('url')
                if not media_url:
                    continue
                manifest_url = (
                    media_url if media_url.startswith('http://') or media_url.startswith('https://')
                    else ((base_url or '/'.join(manifest_url.split('/')[:-1])) + '/' + media_url))
                # If media_url is itself a f4m manifest do the recursive extraction
                # since bitrates in parent manifest (this one) and media_url manifest
                # may differ leading to inability to resolve the format by requested
                # bitrate in f4m downloader
                if determine_ext(manifest_url) == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        manifest_url, video_id, preference=preference, f4m_id=f4m_id,
                        transform_source=transform_source, fatal=fatal))
                    continue
            tbr = int_or_none(media_el.attrib.get('bitrate'))
            formats.append({
                'format_id': '-'.join(filter(None, [f4m_id, compat_str(i if tbr is None else tbr)])),
                'url': manifest_url,
                'ext': 'flv',
                'tbr': tbr,
                'width': int_or_none(media_el.attrib.get('width')),
                'height': int_or_none(media_el.attrib.get('height')),
                'preference': preference,
            })
        return formats

    def _extract_m3u8_formats(self, m3u8_url, video_id, ext=None,
                              entry_protocol='m3u8', preference=None,
                              m3u8_id=None, note=None, errnote=None,
                              fatal=True, live=False):

        formats = [{
            'format_id': '-'.join(filter(None, [m3u8_id, 'meta'])),
            'url': m3u8_url,
            'ext': ext,
            'protocol': 'm3u8',
            'preference': preference - 1 if preference else -1,
            'resolution': 'multiple',
            'format_note': 'Quality selection URL',
        }]

        format_url = lambda u: (
            u
            if re.match(r'^https?://', u)
            else compat_urlparse.urljoin(m3u8_url, u))

        res = self._download_webpage_handle(
            m3u8_url, video_id,
            note=note or 'Downloading m3u8 information',
            errnote=errnote or 'Failed to download m3u8 information',
            fatal=fatal)
        if res is False:
            return []
        m3u8_doc, urlh = res
        m3u8_url = urlh.geturl()

        # We should try extracting formats only from master playlists [1], i.e.
        # playlists that describe available qualities. On the other hand media
        # playlists [2] should be returned as is since they contain just the media
        # without qualities renditions.
        # Fortunately, master playlist can be easily distinguished from media
        # playlist based on particular tags availability. As of [1, 2] master
        # playlist tags MUST NOT appear in a media playist and vice versa.
        # As of [3] #EXT-X-TARGETDURATION tag is REQUIRED for every media playlist
        # and MUST NOT appear in master playlist thus we can clearly detect media
        # playlist with this criterion.
        # 1. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.4
        # 2. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.3
        # 3. https://tools.ietf.org/html/draft-pantos-http-live-streaming-17#section-4.3.3.1
        if '#EXT-X-TARGETDURATION' in m3u8_doc:  # media playlist, return as is
            return [{
                'url': m3u8_url,
                'format_id': m3u8_id,
                'ext': ext,
                'protocol': entry_protocol,
                'preference': preference,
            }]
        last_info = None
        last_media = None
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
            elif line.startswith('#EXT-X-MEDIA:'):
                last_media = {}
                for m in kv_rex.finditer(line):
                    v = m.group('val')
                    if v.startswith('"'):
                        v = v[1:-1]
                    last_media[m.group('key')] = v
            elif line.startswith('#') or not line.strip():
                continue
            else:
                if last_info is None:
                    formats.append({'url': format_url(line)})
                    continue
                tbr = int_or_none(last_info.get('BANDWIDTH'), scale=1000)
                format_id = []
                if m3u8_id:
                    format_id.append(m3u8_id)
                last_media_name = last_media.get('NAME') if last_media and last_media.get('TYPE') != 'SUBTITLES' else None
                # Despite specification does not mention NAME attribute for
                # EXT-X-STREAM-INF it still sometimes may be present
                stream_name = last_info.get('NAME') or last_media_name
                # Bandwidth of live streams may differ over time thus making
                # format_id unpredictable. So it's better to keep provided
                # format_id intact.
                if not live:
                    format_id.append(stream_name if stream_name else '%d' % (tbr if tbr else len(formats)))
                f = {
                    'format_id': '-'.join(format_id),
                    'url': format_url(line.strip()),
                    'tbr': tbr,
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                resolution = last_info.get('RESOLUTION')
                if resolution:
                    width_str, height_str = resolution.split('x')
                    f['width'] = int(width_str)
                    f['height'] = int(height_str)
                codecs = last_info.get('CODECS')
                if codecs:
                    vcodec, acodec = [None] * 2
                    va_codecs = codecs.split(',')
                    if len(va_codecs) == 1:
                        # Audio only entries usually come with single codec and
                        # no resolution. For more robustness we also check it to
                        # be mp4 audio.
                        if not resolution and va_codecs[0].startswith('mp4a'):
                            vcodec, acodec = 'none', va_codecs[0]
                        else:
                            vcodec = va_codecs[0]
                    else:
                        vcodec, acodec = va_codecs[:2]
                    f.update({
                        'acodec': acodec,
                        'vcodec': vcodec,
                    })
                if last_media is not None:
                    f['m3u8_media'] = last_media
                    last_media = None
                formats.append(f)
                last_info = {}
        return formats

    @staticmethod
    def _xpath_ns(path, namespace=None):
        if not namespace:
            return path
        out = []
        for c in path.split('/'):
            if not c or c == '.':
                out.append(c)
            else:
                out.append('{%s}%s' % (namespace, c))
        return '/'.join(out)

    def _extract_smil_formats(self, smil_url, video_id, fatal=True, f4m_params=None, transform_source=None):
        smil = self._download_smil(smil_url, video_id, fatal=fatal, transform_source=transform_source)

        if smil is False:
            assert not fatal
            return []

        namespace = self._parse_smil_namespace(smil)

        return self._parse_smil_formats(
            smil, smil_url, video_id, namespace=namespace, f4m_params=f4m_params)

    def _extract_smil_info(self, smil_url, video_id, fatal=True, f4m_params=None):
        smil = self._download_smil(smil_url, video_id, fatal=fatal)
        if smil is False:
            return {}
        return self._parse_smil(smil, smil_url, video_id, f4m_params=f4m_params)

    def _download_smil(self, smil_url, video_id, fatal=True, transform_source=None):
        return self._download_xml(
            smil_url, video_id, 'Downloading SMIL file',
            'Unable to download SMIL file', fatal=fatal, transform_source=transform_source)

    def _parse_smil(self, smil, smil_url, video_id, f4m_params=None):
        namespace = self._parse_smil_namespace(smil)

        formats = self._parse_smil_formats(
            smil, smil_url, video_id, namespace=namespace, f4m_params=f4m_params)
        subtitles = self._parse_smil_subtitles(smil, namespace=namespace)

        video_id = os.path.splitext(url_basename(smil_url))[0]
        title = None
        description = None
        upload_date = None
        for meta in smil.findall(self._xpath_ns('./head/meta', namespace)):
            name = meta.attrib.get('name')
            content = meta.attrib.get('content')
            if not name or not content:
                continue
            if not title and name == 'title':
                title = content
            elif not description and name in ('description', 'abstract'):
                description = content
            elif not upload_date and name == 'date':
                upload_date = unified_strdate(content)

        thumbnails = [{
            'id': image.get('type'),
            'url': image.get('src'),
            'width': int_or_none(image.get('width')),
            'height': int_or_none(image.get('height')),
        } for image in smil.findall(self._xpath_ns('.//image', namespace)) if image.get('src')]

        return {
            'id': video_id,
            'title': title or video_id,
            'description': description,
            'upload_date': upload_date,
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
        }

    def _parse_smil_namespace(self, smil):
        return self._search_regex(
            r'(?i)^{([^}]+)?}smil$', smil.tag, 'namespace', default=None)

    def _parse_smil_formats(self, smil, smil_url, video_id, namespace=None, f4m_params=None, transform_rtmp_url=None):
        base = smil_url
        for meta in smil.findall(self._xpath_ns('./head/meta', namespace)):
            b = meta.get('base') or meta.get('httpBase')
            if b:
                base = b
                break

        formats = []
        rtmp_count = 0
        http_count = 0
        m3u8_count = 0

        srcs = []
        videos = smil.findall(self._xpath_ns('.//video', namespace))
        for video in videos:
            src = video.get('src')
            if not src or src in srcs:
                continue
            srcs.append(src)

            bitrate = float_or_none(video.get('system-bitrate') or video.get('systemBitrate'), 1000)
            filesize = int_or_none(video.get('size') or video.get('fileSize'))
            width = int_or_none(video.get('width'))
            height = int_or_none(video.get('height'))
            proto = video.get('proto')
            ext = video.get('ext')
            src_ext = determine_ext(src)
            streamer = video.get('streamer') or base

            if proto == 'rtmp' or streamer.startswith('rtmp'):
                rtmp_count += 1
                formats.append({
                    'url': streamer,
                    'play_path': src,
                    'ext': 'flv',
                    'format_id': 'rtmp-%d' % (rtmp_count if bitrate is None else bitrate),
                    'tbr': bitrate,
                    'filesize': filesize,
                    'width': width,
                    'height': height,
                })
                if transform_rtmp_url:
                    streamer, src = transform_rtmp_url(streamer, src)
                    formats[-1].update({
                        'url': streamer,
                        'play_path': src,
                    })
                continue

            src_url = src if src.startswith('http') else compat_urlparse.urljoin(base, src)
            src_url = src_url.strip()

            if proto == 'm3u8' or src_ext == 'm3u8':
                m3u8_formats = self._extract_m3u8_formats(
                    src_url, video_id, ext or 'mp4', m3u8_id='hls', fatal=False)
                if len(m3u8_formats) == 1:
                    m3u8_count += 1
                    m3u8_formats[0].update({
                        'format_id': 'hls-%d' % (m3u8_count if bitrate is None else bitrate),
                        'tbr': bitrate,
                        'width': width,
                        'height': height,
                    })
                formats.extend(m3u8_formats)
                continue

            if src_ext == 'f4m':
                f4m_url = src_url
                if not f4m_params:
                    f4m_params = {
                        'hdcore': '3.2.0',
                        'plugin': 'flowplayer-3.2.0.1',
                    }
                f4m_url += '&' if '?' in f4m_url else '?'
                f4m_url += compat_urllib_parse_urlencode(f4m_params)
                formats.extend(self._extract_f4m_formats(f4m_url, video_id, f4m_id='hds', fatal=False))
                continue

            if src_url.startswith('http') and self._is_valid_url(src, video_id):
                http_count += 1
                formats.append({
                    'url': src_url,
                    'ext': ext or src_ext or 'flv',
                    'format_id': 'http-%d' % (bitrate or http_count),
                    'tbr': bitrate,
                    'filesize': filesize,
                    'width': width,
                    'height': height,
                })
                continue

        return formats

    def _parse_smil_subtitles(self, smil, namespace=None, subtitles_lang='en'):
        urls = []
        subtitles = {}
        for num, textstream in enumerate(smil.findall(self._xpath_ns('.//textstream', namespace))):
            src = textstream.get('src')
            if not src or src in urls:
                continue
            urls.append(src)
            ext = textstream.get('ext') or mimetype2ext(textstream.get('type')) or determine_ext(src)
            lang = textstream.get('systemLanguage') or textstream.get('systemLanguageName') or textstream.get('lang') or subtitles_lang
            subtitles.setdefault(lang, []).append({
                'url': src,
                'ext': ext,
            })
        return subtitles

    def _extract_xspf_playlist(self, playlist_url, playlist_id, fatal=True):
        xspf = self._download_xml(
            playlist_url, playlist_id, 'Downloading xpsf playlist',
            'Unable to download xspf manifest', fatal=fatal)
        if xspf is False:
            return []
        return self._parse_xspf(xspf, playlist_id)

    def _parse_xspf(self, playlist, playlist_id):
        NS_MAP = {
            'xspf': 'http://xspf.org/ns/0/',
            's1': 'http://static.streamone.nl/player/ns/0',
        }

        entries = []
        for track in playlist.findall(xpath_with_ns('./xspf:trackList/xspf:track', NS_MAP)):
            title = xpath_text(
                track, xpath_with_ns('./xspf:title', NS_MAP), 'title', default=playlist_id)
            description = xpath_text(
                track, xpath_with_ns('./xspf:annotation', NS_MAP), 'description')
            thumbnail = xpath_text(
                track, xpath_with_ns('./xspf:image', NS_MAP), 'thumbnail')
            duration = float_or_none(
                xpath_text(track, xpath_with_ns('./xspf:duration', NS_MAP), 'duration'), 1000)

            formats = [{
                'url': location.text,
                'format_id': location.get(xpath_with_ns('s1:label', NS_MAP)),
                'width': int_or_none(location.get(xpath_with_ns('s1:width', NS_MAP))),
                'height': int_or_none(location.get(xpath_with_ns('s1:height', NS_MAP))),
            } for location in track.findall(xpath_with_ns('./xspf:location', NS_MAP))]
            self._sort_formats(formats)

            entries.append({
                'id': playlist_id,
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'duration': duration,
                'formats': formats,
            })
        return entries

    def _extract_mpd_formats(self, mpd_url, video_id, mpd_id=None, note=None, errnote=None, fatal=True, formats_dict={}):
        res = self._download_webpage_handle(
            mpd_url, video_id,
            note=note or 'Downloading MPD manifest',
            errnote=errnote or 'Failed to download MPD manifest',
            fatal=fatal)
        if res is False:
            return []
        mpd, urlh = res
        mpd_base_url = re.match(r'https?://.+/', urlh.geturl()).group()

        return self._parse_mpd_formats(
            compat_etree_fromstring(mpd.encode('utf-8')), mpd_id, mpd_base_url, formats_dict=formats_dict)

    def _parse_mpd_formats(self, mpd_doc, mpd_id=None, mpd_base_url='', formats_dict={}):
        if mpd_doc.get('type') == 'dynamic':
            return []

        namespace = self._search_regex(r'(?i)^{([^}]+)?}MPD$', mpd_doc.tag, 'namespace', default=None)

        def _add_ns(path):
            return self._xpath_ns(path, namespace)

        def is_drm_protected(element):
            return element.find(_add_ns('ContentProtection')) is not None

        def extract_multisegment_info(element, ms_parent_info):
            ms_info = ms_parent_info.copy()
            segment_list = element.find(_add_ns('SegmentList'))
            if segment_list is not None:
                segment_urls_e = segment_list.findall(_add_ns('SegmentURL'))
                if segment_urls_e:
                    ms_info['segment_urls'] = [segment.attrib['media'] for segment in segment_urls_e]
                initialization = segment_list.find(_add_ns('Initialization'))
                if initialization is not None:
                    ms_info['initialization_url'] = initialization.attrib['sourceURL']
            else:
                segment_template = element.find(_add_ns('SegmentTemplate'))
                if segment_template is not None:
                    start_number = segment_template.get('startNumber')
                    if start_number:
                        ms_info['start_number'] = int(start_number)
                    segment_timeline = segment_template.find(_add_ns('SegmentTimeline'))
                    if segment_timeline is not None:
                        s_e = segment_timeline.findall(_add_ns('S'))
                        if s_e:
                            ms_info['total_number'] = 0
                            for s in s_e:
                                ms_info['total_number'] += 1 + int(s.get('r', '0'))
                    else:
                        timescale = segment_template.get('timescale')
                        if timescale:
                            ms_info['timescale'] = int(timescale)
                        segment_duration = segment_template.get('duration')
                        if segment_duration:
                            ms_info['segment_duration'] = int(segment_duration)
                    media_template = segment_template.get('media')
                    if media_template:
                        ms_info['media_template'] = media_template
                    initialization = segment_template.get('initialization')
                    if initialization:
                        ms_info['initialization_url'] = initialization
                    else:
                        initialization = segment_template.find(_add_ns('Initialization'))
                        if initialization is not None:
                            ms_info['initialization_url'] = initialization.attrib['sourceURL']
            return ms_info

        mpd_duration = parse_duration(mpd_doc.get('mediaPresentationDuration'))
        formats = []
        for period in mpd_doc.findall(_add_ns('Period')):
            period_duration = parse_duration(period.get('duration')) or mpd_duration
            period_ms_info = extract_multisegment_info(period, {
                'start_number': 1,
                'timescale': 1,
            })
            for adaptation_set in period.findall(_add_ns('AdaptationSet')):
                if is_drm_protected(adaptation_set):
                    continue
                adaption_set_ms_info = extract_multisegment_info(adaptation_set, period_ms_info)
                for representation in adaptation_set.findall(_add_ns('Representation')):
                    if is_drm_protected(representation):
                        continue
                    representation_attrib = adaptation_set.attrib.copy()
                    representation_attrib.update(representation.attrib)
                    # According to page 41 of ISO/IEC 29001-1:2014, @mimeType is mandatory
                    mime_type = representation_attrib['mimeType']
                    content_type = mime_type.split('/')[0]
                    if content_type == 'text':
                        # TODO implement WebVTT downloading
                        pass
                    elif content_type == 'video' or content_type == 'audio':
                        base_url = ''
                        for element in (representation, adaptation_set, period, mpd_doc):
                            base_url_e = element.find(_add_ns('BaseURL'))
                            if base_url_e is not None:
                                base_url = base_url_e.text + base_url
                                if re.match(r'^https?://', base_url):
                                    break
                        if mpd_base_url and not re.match(r'^https?://', base_url):
                            if not mpd_base_url.endswith('/') and not base_url.startswith('/'):
                                mpd_base_url += '/'
                            base_url = mpd_base_url + base_url
                        representation_id = representation_attrib.get('id')
                        lang = representation_attrib.get('lang')
                        url_el = representation.find(_add_ns('BaseURL'))
                        filesize = int_or_none(url_el.attrib.get('{http://youtube.com/yt/2012/10/10}contentLength') if url_el is not None else None)
                        f = {
                            'format_id': '%s-%s' % (mpd_id, representation_id) if mpd_id else representation_id,
                            'url': base_url,
                            'ext': mimetype2ext(mime_type),
                            'width': int_or_none(representation_attrib.get('width')),
                            'height': int_or_none(representation_attrib.get('height')),
                            'tbr': int_or_none(representation_attrib.get('bandwidth'), 1000),
                            'asr': int_or_none(representation_attrib.get('audioSamplingRate')),
                            'fps': int_or_none(representation_attrib.get('frameRate')),
                            'vcodec': 'none' if content_type == 'audio' else representation_attrib.get('codecs'),
                            'acodec': 'none' if content_type == 'video' else representation_attrib.get('codecs'),
                            'language': lang if lang not in ('mul', 'und', 'zxx', 'mis') else None,
                            'format_note': 'DASH %s' % content_type,
                            'filesize': filesize,
                        }
                        representation_ms_info = extract_multisegment_info(representation, adaption_set_ms_info)
                        if 'segment_urls' not in representation_ms_info and 'media_template' in representation_ms_info:
                            if 'total_number' not in representation_ms_info and 'segment_duration':
                                segment_duration = float(representation_ms_info['segment_duration']) / float(representation_ms_info['timescale'])
                                representation_ms_info['total_number'] = int(math.ceil(float(period_duration) / segment_duration))
                            media_template = representation_ms_info['media_template']
                            media_template = media_template.replace('$RepresentationID$', representation_id)
                            media_template = re.sub(r'\$(Number|Bandwidth)\$', r'%(\1)d', media_template)
                            media_template = re.sub(r'\$(Number|Bandwidth)%([^$]+)\$', r'%(\1)\2', media_template)
                            media_template.replace('$$', '$')
                            representation_ms_info['segment_urls'] = [
                                media_template % {
                                    'Number': segment_number,
                                    'Bandwidth': representation_attrib.get('bandwidth')}
                                for segment_number in range(
                                    representation_ms_info['start_number'],
                                    representation_ms_info['total_number'] + representation_ms_info['start_number'])]
                        if 'segment_urls' in representation_ms_info:
                            f.update({
                                'segment_urls': representation_ms_info['segment_urls'],
                                'protocol': 'http_dash_segments',
                            })
                            if 'initialization_url' in representation_ms_info:
                                initialization_url = representation_ms_info['initialization_url'].replace('$RepresentationID$', representation_id)
                                f.update({
                                    'initialization_url': initialization_url,
                                })
                                if not f.get('url'):
                                    f['url'] = initialization_url
                        try:
                            existing_format = next(
                                fo for fo in formats
                                if fo['format_id'] == representation_id)
                        except StopIteration:
                            full_info = formats_dict.get(representation_id, {}).copy()
                            full_info.update(f)
                            formats.append(full_info)
                        else:
                            existing_format.update(f)
                    else:
                        self.report_warning('Unknown MIME type %s in DASH manifest' % mime_type)
        return formats

    def _live_title(self, name):
        """ Generate the title for a live video """
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d %H:%M')
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

    def _get_cookies(self, url):
        """ Return a compat_cookies.SimpleCookie with the cookies for the url """
        req = sanitized_Request(url)
        self._downloader.cookiejar.add_cookie_header(req)
        return compat_cookies.SimpleCookie(req.get_header('Cookie'))

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

    def extract_subtitles(self, *args, **kwargs):
        if (self._downloader.params.get('writesubtitles', False) or
                self._downloader.params.get('listsubtitles')):
            return self._get_subtitles(*args, **kwargs)
        return {}

    def _get_subtitles(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented by subclasses')

    @staticmethod
    def _merge_subtitle_items(subtitle_list1, subtitle_list2):
        """ Merge subtitle items for one language. Items with duplicated URLs
        will be dropped. """
        list1_urls = set([item['url'] for item in subtitle_list1])
        ret = list(subtitle_list1)
        ret.extend([item for item in subtitle_list2 if item['url'] not in list1_urls])
        return ret

    @classmethod
    def _merge_subtitles(cls, subtitle_dict1, subtitle_dict2):
        """ Merge two subtitle dictionaries, language by language. """
        ret = dict(subtitle_dict1)
        for lang in subtitle_dict2:
            ret[lang] = cls._merge_subtitle_items(subtitle_dict1.get(lang, []), subtitle_dict2[lang])
        return ret

    def extract_automatic_captions(self, *args, **kwargs):
        if (self._downloader.params.get('writeautomaticsub', False) or
                self._downloader.params.get('listsubtitles')):
            return self._get_automatic_captions(*args, **kwargs)
        return {}

    def _get_automatic_captions(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented by subclasses')

    def mark_watched(self, *args, **kwargs):
        if (self._downloader.params.get('mark_watched', False) and
                (self._get_login_info()[0] is not None or
                    self._downloader.params.get('cookiefile') is not None)):
            self._mark_watched(*args, **kwargs)

    def _mark_watched(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented by subclasses')


class SearchInfoExtractor(InfoExtractor):
    """
    Base class for paged search queries extractors.
    They accept URLs in the format _SEARCH_KEY(|all|[0-9]):{query}
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
        raise NotImplementedError('This method must be implemented by subclasses')

    @property
    def SEARCH_KEY(self):
        return self._SEARCH_KEY
