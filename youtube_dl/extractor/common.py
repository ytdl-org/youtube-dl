# coding: utf-8
from __future__ import unicode_literals

import base64
import datetime
import hashlib
import json
import netrc
import os
import random
import re
import socket
import ssl
import sys
import time
import math

from ..compat import (
    compat_cookiejar_Cookie,
    compat_cookies_SimpleCookie,
    compat_etree_Element,
    compat_etree_fromstring,
    compat_getpass,
    compat_integer_types,
    compat_http_client,
    compat_os_name,
    compat_str,
    compat_urllib_error,
    compat_urllib_parse_unquote,
    compat_urllib_parse_urlencode,
    compat_urllib_request,
    compat_urlparse,
    compat_xml_parse_error,
)
from ..downloader.f4m import (
    get_base_url,
    remove_encrypted_media,
)
from ..utils import (
    NO_DEFAULT,
    age_restricted,
    base_url,
    bug_reports_message,
    clean_html,
    compiled_regex_type,
    determine_ext,
    determine_protocol,
    dict_get,
    error_to_compat_str,
    ExtractorError,
    extract_attributes,
    fix_xml_ampersands,
    float_or_none,
    GeoRestrictedError,
    GeoUtils,
    int_or_none,
    js_to_json,
    JSON_LD_RE,
    mimetype2ext,
    orderedSet,
    parse_bitrate,
    parse_codecs,
    parse_duration,
    parse_iso8601,
    parse_m3u8_attributes,
    parse_resolution,
    RegexNotFoundError,
    sanitized_Request,
    sanitize_filename,
    str_or_none,
    str_to_int,
    strip_or_none,
    try_get,
    unescapeHTML,
    unified_strdate,
    unified_timestamp,
    update_Request,
    update_url_query,
    urljoin,
    url_basename,
    url_or_none,
    xpath_element,
    xpath_text,
    xpath_with_ns,
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
                    * url        The mandatory URL representing the media:
                                   for plain file media - HTTP URL of this file,
                                   for RTMP - RTMP URL,
                                   for HLS - URL of the M3U8 media playlist,
                                   for HDS - URL of the F4M manifest,
                                   for DASH
                                     - HTTP URL to plain file media (in case of
                                       unfragmented media)
                                     - URL of the MPD manifest or base URL
                                       representing the media if MPD manifest
                                       is parsed from a string (in case of
                                       fragmented media)
                                   for MSS - URL of the ISM manifest.
                    * manifest_url
                                 The URL of the manifest file in case of
                                 fragmented media:
                                   for HLS - URL of the M3U8 master playlist,
                                   for HDS - URL of the F4M manifest,
                                   for DASH - URL of the MPD manifest,
                                   for MSS - URL of the ISM manifest.
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
                    * fragment_base_url
                                 Base URL for fragments. Each fragment's path
                                 value (if present) will be relative to
                                 this URL.
                    * fragments  A list of fragments of a fragmented media.
                                 Each fragment entry must contain either an url
                                 or a path. If an url is present it should be
                                 considered by a client. Otherwise both path and
                                 fragment_base_url must be present. Here is
                                 the list of all potential fields:
                                 * "url" - fragment's URL
                                 * "path" - fragment's path relative to
                                            fragment_base_url
                                 * "duration" (optional, int or float)
                                 * "filesize" (optional, int)
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
                    * downloader_options  A dictionary of downloader options as
                                 described in FileDownloader

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
                        * "resolution" (optional, string "{width}x{height}",
                                        deprecated)
                        * "filesize" (optional, int)
    thumbnail:      Full URL to a video thumbnail image.
    description:    Full video description.
    uploader:       Full name of the video uploader.
    license:        License name the video is licensed under.
    creator:        The creator of the video.
    release_timestamp: UNIX timestamp of the moment the video was released.
    release_date:   The date (YYYYMMDD) when the video was released.
    timestamp:      UNIX timestamp of the moment the video became available
                    (uploaded).
    upload_date:    Video upload date (YYYYMMDD).
                    If not explicitly set, calculated from timestamp.
    uploader_id:    Nickname or id of the video uploader.
    uploader_url:   Full URL to a personal webpage of the video uploader.
    channel:        Full name of the channel the video is uploaded on.
                    Note that channel fields may or may not repeat uploader
                    fields. This depends on a particular extractor.
    channel_id:     Id of the channel.
    channel_url:    Full URL to a channel webpage.
    location:       Physical location where the video was filmed.
    subtitles:      The available subtitles as a dictionary in the format
                    {tag: subformats}. "tag" is usually a language code, and
                    "subformats" is a list sorted from lower to higher
                    preference, each element is a dictionary with the "ext"
                    entry and one of:
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
    chapters:       A list of dictionaries, with the following entries:
                        * "start_time" - The start time of the chapter in seconds
                        * "end_time" - The end time of the chapter in seconds
                        * "title" (optional, string)

    The following fields should only be used when the video belongs to some logical
    chapter or section:

    chapter:        Name or title of the chapter the video belongs to.
    chapter_number: Number of the chapter the video belongs to, as an integer.
    chapter_id:     Id of the chapter the video belongs to, as a unicode string.

    The following fields should only be used when the video is an episode of some
    series, programme or podcast:

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

    Additionally, playlists can have "id", "title", "description", "uploader",
    "uploader_id", "uploader_url", "duration" attributes with the same semantics
    as videos (see above).


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

    _GEO_BYPASS attribute may be set to False in order to disable
    geo restriction bypass mechanisms for a particular extractor.
    Though it won't disable explicit geo restriction bypass based on
    country code provided with geo_bypass_country.

    _GEO_COUNTRIES attribute may contain a list of presumably geo unrestricted
    countries for this extractor. One of these countries will be used by
    geo restriction bypass mechanism right away in order to bypass
    geo restriction, of course, if the mechanism is not disabled.

    _GEO_IP_BLOCKS attribute may contain a list of presumably geo unrestricted
    IP blocks in CIDR notation for this extractor. One of these IP blocks
    will be used by geo restriction bypass mechanism similarly
    to _GEO_COUNTRIES.

    Finally, the _WORKING attribute should be set to False for broken IEs
    in order to warn the users and skip the tests.
    """

    _ready = False
    _downloader = None
    _x_forwarded_for_ip = None
    _GEO_BYPASS = True
    _GEO_COUNTRIES = None
    _GEO_IP_BLOCKS = None
    _WORKING = True

    def __init__(self, downloader=None):
        """Constructor. Receives an optional downloader."""
        self._ready = False
        self._x_forwarded_for_ip = None
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
        return compat_str(m.group('id'))

    @classmethod
    def working(cls):
        """Getter method for _WORKING."""
        return cls._WORKING

    def initialize(self):
        """Initializes an instance (authentication, etc)."""
        self._initialize_geo_bypass({
            'countries': self._GEO_COUNTRIES,
            'ip_blocks': self._GEO_IP_BLOCKS,
        })
        if not self._ready:
            self._real_initialize()
            self._ready = True

    def _initialize_geo_bypass(self, geo_bypass_context):
        """
        Initialize geo restriction bypass mechanism.

        This method is used to initialize geo bypass mechanism based on faking
        X-Forwarded-For HTTP header. A random country from provided country list
        is selected and a random IP belonging to this country is generated. This
        IP will be passed as X-Forwarded-For HTTP header in all subsequent
        HTTP requests.

        This method will be used for initial geo bypass mechanism initialization
        during the instance initialization with _GEO_COUNTRIES and
        _GEO_IP_BLOCKS.

        You may also manually call it from extractor's code if geo bypass
        information is not available beforehand (e.g. obtained during
        extraction) or due to some other reason. In this case you should pass
        this information in geo bypass context passed as first argument. It may
        contain following fields:

        countries:  List of geo unrestricted countries (similar
                    to _GEO_COUNTRIES)
        ip_blocks:  List of geo unrestricted IP blocks in CIDR notation
                    (similar to _GEO_IP_BLOCKS)

        """
        if not self._x_forwarded_for_ip:

            # Geo bypass mechanism is explicitly disabled by user
            if not self._downloader.params.get('geo_bypass', True):
                return

            if not geo_bypass_context:
                geo_bypass_context = {}

            # Backward compatibility: previously _initialize_geo_bypass
            # expected a list of countries, some 3rd party code may still use
            # it this way
            if isinstance(geo_bypass_context, (list, tuple)):
                geo_bypass_context = {
                    'countries': geo_bypass_context,
                }

            # The whole point of geo bypass mechanism is to fake IP
            # as X-Forwarded-For HTTP header based on some IP block or
            # country code.

            # Path 1: bypassing based on IP block in CIDR notation

            # Explicit IP block specified by user, use it right away
            # regardless of whether extractor is geo bypassable or not
            ip_block = self._downloader.params.get('geo_bypass_ip_block', None)

            # Otherwise use random IP block from geo bypass context but only
            # if extractor is known as geo bypassable
            if not ip_block:
                ip_blocks = geo_bypass_context.get('ip_blocks')
                if self._GEO_BYPASS and ip_blocks:
                    ip_block = random.choice(ip_blocks)

            if ip_block:
                self._x_forwarded_for_ip = GeoUtils.random_ipv4(ip_block)
                if self._downloader.params.get('verbose', False):
                    self._downloader.to_screen(
                        '[debug] Using fake IP %s as X-Forwarded-For.'
                        % self._x_forwarded_for_ip)
                return

            # Path 2: bypassing based on country code

            # Explicit country code specified by user, use it right away
            # regardless of whether extractor is geo bypassable or not
            country = self._downloader.params.get('geo_bypass_country', None)

            # Otherwise use random country code from geo bypass context but
            # only if extractor is known as geo bypassable
            if not country:
                countries = geo_bypass_context.get('countries')
                if self._GEO_BYPASS and countries:
                    country = random.choice(countries)

            if country:
                self._x_forwarded_for_ip = GeoUtils.random_ipv4(country)
                if self._downloader.params.get('verbose', False):
                    self._downloader.to_screen(
                        '[debug] Using fake IP %s (%s) as X-Forwarded-For.'
                        % (self._x_forwarded_for_ip, country.upper()))

    def extract(self, url):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url)
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except ExtractorError:
            raise
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e, expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e)

    def __maybe_fake_ip_and_retry(self, countries):
        if (not self._downloader.params.get('geo_bypass_country', None)
                and self._GEO_BYPASS
                and self._downloader.params.get('geo_bypass', True)
                and not self._x_forwarded_for_ip
                and countries):
            country_code = random.choice(countries)
            self._x_forwarded_for_ip = GeoUtils.random_ipv4(country_code)
            if self._x_forwarded_for_ip:
                self.report_warning(
                    'Video is geo restricted. Retrying extraction with fake IP %s (%s) as X-Forwarded-For.'
                    % (self._x_forwarded_for_ip, country_code.upper()))
                return True
        return False

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

    @staticmethod
    def __can_accept_status_code(err, expected_status):
        assert isinstance(err, compat_urllib_error.HTTPError)
        if expected_status is None:
            return False
        if isinstance(expected_status, compat_integer_types):
            return err.code == expected_status
        elif isinstance(expected_status, (list, tuple)):
            return err.code in expected_status
        elif callable(expected_status):
            return expected_status(err.code) is True
        else:
            assert False

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}, expected_status=None):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            if 'X-Forwarded-For' not in headers:
                headers['X-Forwarded-For'] = self._x_forwarded_for_ip

        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
            if data is not None or headers:
                url_or_request = sanitized_Request(url_or_request, data, headers)
        exceptions = [compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error]
        if hasattr(ssl, 'CertificateError'):
            exceptions.append(ssl.CertificateError)
        try:
            return self._downloader.urlopen(url_or_request)
        except tuple(exceptions) as err:
            if isinstance(err, compat_urllib_error.HTTPError):
                if self.__can_accept_status_code(err, expected_status):
                    # Retain reference to error to prevent file object from
                    # being closed before it can be read. Works around the
                    # effects of <https://bugs.python.org/issue15002>
                    # introduced in Python 3.4.1.
                    err.fp._error = err
                    return err.fp

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

    def _download_webpage_handle(self, url_or_request, video_id, note=None, errnote=None, fatal=True, encoding=None, data=None, headers={}, query={}, expected_status=None):
        """
        Return a tuple (page content as string, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        # Strip hashes from the URL (#1038)
        if isinstance(url_or_request, (compat_str, str)):
            url_or_request = url_or_request.partition('#')[0]

        urlh = self._request_webpage(url_or_request, video_id, note, errnote, fatal, data=data, headers=headers, query=query, expected_status=expected_status)
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

    def __check_blocked(self, content):
        first_block = content[:512]
        if ('<title>Access to this site is blocked</title>' in content
                and 'Websense' in first_block):
            msg = 'Access to this webpage has been blocked by Websense filtering software in your network.'
            blocked_iframe = self._html_search_regex(
                r'<iframe src="([^"]+)"', content,
                'Websense information URL', default=None)
            if blocked_iframe:
                msg += ' Visit %s for more details' % blocked_iframe
            raise ExtractorError(msg, expected=True)
        if '<title>The URL you requested has been blocked</title>' in first_block:
            msg = (
                'Access to this webpage has been blocked by Indian censorship. '
                'Use a VPN or proxy server (with --proxy) to route around it.')
            block_msg = self._html_search_regex(
                r'</h1><p>(.*?)</p>',
                content, 'block message', default=None)
            if block_msg:
                msg += ' (Message: "%s")' % block_msg.replace('\n', ' ')
            raise ExtractorError(msg, expected=True)
        if ('<title>TTK :: Доступ к ресурсу ограничен</title>' in content
                and 'blocklist.rkn.gov.ru' in content):
            raise ExtractorError(
                'Access to this webpage has been blocked by decision of the Russian government. '
                'Visit http://blocklist.rkn.gov.ru/ for a block reason.',
                expected=True)

    def _webpage_read_content(self, urlh, url_or_request, video_id, note=None, errnote=None, fatal=True, prefix=None, encoding=None):
        content_type = urlh.headers.get('Content-Type', '')
        webpage_bytes = urlh.read()
        if prefix is not None:
            webpage_bytes = prefix + webpage_bytes
        if not encoding:
            encoding = self._guess_encoding_from_content(content_type, webpage_bytes)
        if self._downloader.params.get('dump_intermediate_pages', False):
            self.to_screen('Dumping request to ' + urlh.geturl())
            dump = base64.b64encode(webpage_bytes).decode('ascii')
            self._downloader.to_screen(dump)
        if self._downloader.params.get('write_pages', False):
            basen = '%s_%s' % (video_id, urlh.geturl())
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

        self.__check_blocked(content)

        return content

    def _download_webpage(
            self, url_or_request, video_id, note=None, errnote=None,
            fatal=True, tries=1, timeout=5, encoding=None, data=None,
            headers={}, query={}, expected_status=None):
        """
        Return the data of the page as a string.

        Arguments:
        url_or_request -- plain text URL as a string or
            a compat_urllib_request.Requestobject
        video_id -- Video/playlist/item identifier (string)

        Keyword arguments:
        note -- note printed before downloading (string)
        errnote -- note printed in case of an error (string)
        fatal -- flag denoting whether error should be considered fatal,
            i.e. whether it should cause ExtractionError to be raised,
            otherwise a warning will be reported and extraction continued
        tries -- number of tries
        timeout -- sleep interval between tries
        encoding -- encoding for a page content decoding, guessed automatically
            when not explicitly specified
        data -- POST data (bytes)
        headers -- HTTP headers (dict)
        query -- URL query (dict)
        expected_status -- allows to accept failed HTTP requests (non 2xx
            status code) by explicitly specifying a set of accepted status
            codes. Can be any of the following entities:
                - an integer type specifying an exact failed status code to
                  accept
                - a list or a tuple of integer types specifying a list of
                  failed status codes to accept
                - a callable accepting an actual failed status code and
                  returning True if it should be accepted
            Note that this argument does not affect success status codes (2xx)
            which are always accepted.
        """

        success = False
        try_count = 0
        while success is False:
            try:
                res = self._download_webpage_handle(
                    url_or_request, video_id, note, errnote, fatal,
                    encoding=encoding, data=data, headers=headers, query=query,
                    expected_status=expected_status)
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

    def _download_xml_handle(
            self, url_or_request, video_id, note='Downloading XML',
            errnote='Unable to download XML', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (xml as an compat_etree_Element, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        xml_string, urlh = res
        return self._parse_xml(
            xml_string, video_id, transform_source=transform_source,
            fatal=fatal), urlh

    def _download_xml(
            self, url_or_request, video_id,
            note='Downloading XML', errnote='Unable to download XML',
            transform_source=None, fatal=True, encoding=None,
            data=None, headers={}, query={}, expected_status=None):
        """
        Return the xml as an compat_etree_Element.

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_xml_handle(
            url_or_request, video_id, note=note, errnote=errnote,
            transform_source=transform_source, fatal=fatal, encoding=encoding,
            data=data, headers=headers, query=query,
            expected_status=expected_status)
        return res if res is False else res[0]

    def _parse_xml(self, xml_string, video_id, transform_source=None, fatal=True):
        if transform_source:
            xml_string = transform_source(xml_string)
        try:
            return compat_etree_fromstring(xml_string.encode('utf-8'))
        except compat_xml_parse_error as ve:
            errmsg = '%s: Failed to parse XML ' % video_id
            if fatal:
                raise ExtractorError(errmsg, cause=ve)
            else:
                self.report_warning(errmsg + str(ve))

    def _download_json_handle(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (JSON object, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        json_string, urlh = res
        return self._parse_json(
            json_string, video_id, transform_source=transform_source,
            fatal=fatal), urlh

    def _download_json(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return the JSON object as a dict.

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_json_handle(
            url_or_request, video_id, note=note, errnote=errnote,
            transform_source=transform_source, fatal=fatal, encoding=encoding,
            data=data, headers=headers, query=query,
            expected_status=expected_status)
        return res if res is False else res[0]

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
    def raise_geo_restricted(msg='This video is not available from your location due to geo restriction', countries=None):
        raise GeoRestrictedError(msg, countries=countries)

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

    def playlist_from_matches(self, matches, playlist_id=None, playlist_title=None, getter=None, ie=None):
        urls = orderedSet(
            self.url_result(self._proto_relative_url(getter(m) if getter else m), ie)
            for m in matches)
        return self.playlist_result(
            urls, playlist_id=playlist_id, playlist_title=playlist_title)

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

    def _get_netrc_login_info(self, netrc_machine=None):
        username = None
        password = None
        netrc_machine = netrc_machine or self._NETRC_MACHINE

        if self._downloader.params.get('usenetrc', False):
            try:
                info = netrc.netrc().authenticators(netrc_machine)
                if info is not None:
                    username = info[0]
                    password = info[2]
                else:
                    raise netrc.NetrcParseError(
                        'No authenticators for %s' % netrc_machine)
            except (IOError, netrc.NetrcParseError) as err:
                self._downloader.report_warning(
                    'parsing .netrc: %s' % error_to_compat_str(err))

        return username, password

    def _get_login_info(self, username_option='username', password_option='password', netrc_machine=None):
        """
        Get the login info as (username, password)
        First look for the manually specified credentials using username_option
        and password_option as keys in params dictionary. If no such credentials
        available look in the netrc file using the netrc_machine or _NETRC_MACHINE
        value.
        If there's no info available, return (None, None)
        """
        if self._downloader is None:
            return (None, None)

        downloader_params = self._downloader.params

        # Attempt to use provided username and password or .netrc data
        if downloader_params.get(username_option) is not None:
            username = downloader_params[username_option]
            password = downloader_params[password_option]
        else:
            username, password = self._get_netrc_login_info(netrc_machine)

        return username, password

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
        content_re = r'content=(?:"([^"]+?)"|\'([^\']+?)\'|\s*([^\s"\'=<>`]+?)(?=\s|/?>))'
        property_re = (r'(?:name|property)=(?:\'og[:-]%(prop)s\'|"og[:-]%(prop)s"|\s*og[:-]%(prop)s\b)'
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
        if not isinstance(prop, (list, tuple)):
            prop = [prop]
        if name is None:
            name = 'OpenGraph %s' % prop[0]
        og_regexes = []
        for p in prop:
            og_regexes.extend(self._og_regexes(p))
        escaped = self._search_regex(og_regexes, html, name, flags=re.DOTALL, **kargs)
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
        if not isinstance(name, (list, tuple)):
            name = [name]
        if display_name is None:
            display_name = name[0]
        return self._html_search_regex(
            [self._meta_regex(n) for n in name],
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
        family_friendly = self._html_search_meta(
            'isFamilyFriendly', html, default=None)

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

    def _search_json_ld(self, html, video_id, expected_type=None, **kwargs):
        json_ld_list = list(re.finditer(JSON_LD_RE, html))
        default = kwargs.get('default', NO_DEFAULT)
        # JSON-LD may be malformed and thus `fatal` should be respected.
        # At the same time `default` may be passed that assumes `fatal=False`
        # for _search_regex. Let's simulate the same behavior here as well.
        fatal = kwargs.get('fatal', True) if default == NO_DEFAULT else False
        json_ld = []
        for mobj in json_ld_list:
            json_ld_item = self._parse_json(
                mobj.group('json_ld'), video_id, fatal=fatal)
            if not json_ld_item:
                continue
            if isinstance(json_ld_item, dict):
                json_ld.append(json_ld_item)
            elif isinstance(json_ld_item, (list, tuple)):
                json_ld.extend(json_ld_item)
        if json_ld:
            json_ld = self._json_ld(json_ld, video_id, fatal=fatal, expected_type=expected_type)
        if json_ld:
            return json_ld
        if default is not NO_DEFAULT:
            return default
        elif fatal:
            raise RegexNotFoundError('Unable to extract JSON-LD')
        else:
            self._downloader.report_warning('unable to extract JSON-LD %s' % bug_reports_message())
            return {}

    def _json_ld(self, json_ld, video_id, fatal=True, expected_type=None):
        if isinstance(json_ld, compat_str):
            json_ld = self._parse_json(json_ld, video_id, fatal=fatal)
        if not json_ld:
            return {}
        info = {}
        if not isinstance(json_ld, (list, tuple, dict)):
            return info
        if isinstance(json_ld, dict):
            json_ld = [json_ld]

        INTERACTION_TYPE_MAP = {
            'CommentAction': 'comment',
            'AgreeAction': 'like',
            'DisagreeAction': 'dislike',
            'LikeAction': 'like',
            'DislikeAction': 'dislike',
            'ListenAction': 'view',
            'WatchAction': 'view',
            'ViewAction': 'view',
        }

        def extract_interaction_type(e):
            interaction_type = e.get('interactionType')
            if isinstance(interaction_type, dict):
                interaction_type = interaction_type.get('@type')
            return str_or_none(interaction_type)

        def extract_interaction_statistic(e):
            interaction_statistic = e.get('interactionStatistic')
            if isinstance(interaction_statistic, dict):
                interaction_statistic = [interaction_statistic]
            if not isinstance(interaction_statistic, list):
                return
            for is_e in interaction_statistic:
                if not isinstance(is_e, dict):
                    continue
                if is_e.get('@type') != 'InteractionCounter':
                    continue
                interaction_type = extract_interaction_type(is_e)
                if not interaction_type:
                    continue
                # For interaction count some sites provide string instead of
                # an integer (as per spec) with non digit characters (e.g. ",")
                # so extracting count with more relaxed str_to_int
                interaction_count = str_to_int(is_e.get('userInteractionCount'))
                if interaction_count is None:
                    continue
                count_kind = INTERACTION_TYPE_MAP.get(interaction_type.split('/')[-1])
                if not count_kind:
                    continue
                count_key = '%s_count' % count_kind
                if info.get(count_key) is not None:
                    continue
                info[count_key] = interaction_count

        def extract_video_object(e):
            assert e['@type'] == 'VideoObject'
            author = e.get('author')
            info.update({
                'url': url_or_none(e.get('contentUrl')),
                'title': unescapeHTML(e.get('name')),
                'description': unescapeHTML(e.get('description')),
                'thumbnail': url_or_none(e.get('thumbnailUrl') or e.get('thumbnailURL')),
                'duration': parse_duration(e.get('duration')),
                'timestamp': unified_timestamp(e.get('uploadDate')),
                # author can be an instance of 'Organization' or 'Person' types.
                # both types can have 'name' property(inherited from 'Thing' type). [1]
                # however some websites are using 'Text' type instead.
                # 1. https://schema.org/VideoObject
                'uploader': author.get('name') if isinstance(author, dict) else author if isinstance(author, compat_str) else None,
                'filesize': float_or_none(e.get('contentSize')),
                'tbr': int_or_none(e.get('bitrate')),
                'width': int_or_none(e.get('width')),
                'height': int_or_none(e.get('height')),
                'view_count': int_or_none(e.get('interactionCount')),
            })
            extract_interaction_statistic(e)

        for e in json_ld:
            if '@context' in e:
                item_type = e.get('@type')
                if expected_type is not None and expected_type != item_type:
                    continue
                if item_type in ('TVEpisode', 'Episode'):
                    episode_name = unescapeHTML(e.get('name'))
                    info.update({
                        'episode': episode_name,
                        'episode_number': int_or_none(e.get('episodeNumber')),
                        'description': unescapeHTML(e.get('description')),
                    })
                    if not info.get('title') and episode_name:
                        info['title'] = episode_name
                    part_of_season = e.get('partOfSeason')
                    if isinstance(part_of_season, dict) and part_of_season.get('@type') in ('TVSeason', 'Season', 'CreativeWorkSeason'):
                        info.update({
                            'season': unescapeHTML(part_of_season.get('name')),
                            'season_number': int_or_none(part_of_season.get('seasonNumber')),
                        })
                    part_of_series = e.get('partOfSeries') or e.get('partOfTVSeries')
                    if isinstance(part_of_series, dict) and part_of_series.get('@type') in ('TVSeries', 'Series', 'CreativeWorkSeries'):
                        info['series'] = unescapeHTML(part_of_series.get('name'))
                elif item_type == 'Movie':
                    info.update({
                        'title': unescapeHTML(e.get('name')),
                        'description': unescapeHTML(e.get('description')),
                        'duration': parse_duration(e.get('duration')),
                        'timestamp': unified_timestamp(e.get('dateCreated')),
                    })
                elif item_type in ('Article', 'NewsArticle'):
                    info.update({
                        'timestamp': parse_iso8601(e.get('datePublished')),
                        'title': unescapeHTML(e.get('headline')),
                        'description': unescapeHTML(e.get('articleBody')),
                    })
                elif item_type == 'VideoObject':
                    extract_video_object(e)
                    if expected_type is None:
                        continue
                    else:
                        break
                video = e.get('video')
                if isinstance(video, dict) and video.get('@type') == 'VideoObject':
                    extract_video_object(video)
                if expected_type is None:
                    continue
                else:
                    break
        return dict((k, v) for k, v in info.items() if v is not None)

    @staticmethod
    def _hidden_inputs(html):
        html = re.sub(r'<!--(?:(?!<!--).)*-->', '', html)
        hidden_inputs = {}
        for input in re.findall(r'(?i)(<input[^>]+>)', html):
            attrs = extract_attributes(input)
            if not input:
                continue
            if attrs.get('type') not in ('hidden', 'submit'):
                continue
            name = attrs.get('name') or attrs.get('id')
            value = attrs.get('value')
            if name and value is not None:
                hidden_inputs[name] = value
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
                return tuple(
                    f.get(field)
                    if f.get(field) is not None
                    else ('' if field == 'format_id' else -1)
                    for field in field_preference)

            preference = f.get('preference')
            if preference is None:
                preference = 0
                if f.get('ext') in ['f4f', 'f4m']:  # Not yet supported
                    preference -= 0.5

            protocol = f.get('protocol') or determine_protocol(f)
            proto_preference = 0 if protocol in ['http', 'https'] else (-0.5 if protocol == 'rtsp' else -0.1)

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

    def _is_valid_url(self, url, video_id, item='video', headers={}):
        url = self._proto_relative_url(url, scheme='http:')
        # For now assume non HTTP(S) URLs always valid
        if not (url.startswith('http://') or url.startswith('https://')):
            return True
        try:
            self._request_webpage(url, video_id, 'Checking %s URL' % item, headers=headers)
            return True
        except ExtractorError as e:
            self.to_screen(
                '%s: %s URL is invalid, skipping: %s'
                % (video_id, item, error_to_compat_str(e.cause)))
            return False

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
                             fatal=True, m3u8_id=None, data=None, headers={}, query={}):
        manifest = self._download_xml(
            manifest_url, video_id, 'Downloading f4m manifest',
            'Unable to download f4m manifest',
            # Some manifests may be malformed, e.g. prosiebensat1 generated manifests
            # (see https://github.com/ytdl-org/youtube-dl/issues/6215#issuecomment-121704244)
            transform_source=transform_source,
            fatal=fatal, data=data, headers=headers, query=query)

        if manifest is False:
            return []

        return self._parse_f4m_formats(
            manifest, manifest_url, video_id, preference=preference, f4m_id=f4m_id,
            transform_source=transform_source, fatal=fatal, m3u8_id=m3u8_id)

    def _parse_f4m_formats(self, manifest, manifest_url, video_id, preference=None, f4m_id=None,
                           transform_source=lambda s: fix_xml_ampersands(s).strip(),
                           fatal=True, m3u8_id=None):
        if not isinstance(manifest, compat_etree_Element) and not fatal:
            return []

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
        # rendition (see https://github.com/ytdl-org/youtube-dl/issues/8573).
        media_nodes = remove_encrypted_media(media_nodes)
        if not media_nodes:
            return formats

        manifest_base_url = get_base_url(manifest)

        bootstrap_info = xpath_element(
            manifest, ['{http://ns.adobe.com/f4m/1.0}bootstrapInfo', '{http://ns.adobe.com/f4m/2.0}bootstrapInfo'],
            'bootstrap info', default=None)

        vcodec = None
        mime_type = xpath_text(
            manifest, ['{http://ns.adobe.com/f4m/1.0}mimeType', '{http://ns.adobe.com/f4m/2.0}mimeType'],
            'base URL', default=None)
        if mime_type and mime_type.startswith('audio/'):
            vcodec = 'none'

        for i, media_el in enumerate(media_nodes):
            tbr = int_or_none(media_el.attrib.get('bitrate'))
            width = int_or_none(media_el.attrib.get('width'))
            height = int_or_none(media_el.attrib.get('height'))
            format_id = '-'.join(filter(None, [f4m_id, compat_str(i if tbr is None else tbr)]))
            # If <bootstrapInfo> is present, the specified f4m is a
            # stream-level manifest, and only set-level manifests may refer to
            # external resources.  See section 11.4 and section 4 of F4M spec
            if bootstrap_info is None:
                media_url = None
                # @href is introduced in 2.0, see section 11.6 of F4M spec
                if manifest_version == '2.0':
                    media_url = media_el.attrib.get('href')
                if media_url is None:
                    media_url = media_el.attrib.get('url')
                if not media_url:
                    continue
                manifest_url = (
                    media_url if media_url.startswith('http://') or media_url.startswith('https://')
                    else ((manifest_base_url or '/'.join(manifest_url.split('/')[:-1])) + '/' + media_url))
                # If media_url is itself a f4m manifest do the recursive extraction
                # since bitrates in parent manifest (this one) and media_url manifest
                # may differ leading to inability to resolve the format by requested
                # bitrate in f4m downloader
                ext = determine_ext(manifest_url)
                if ext == 'f4m':
                    f4m_formats = self._extract_f4m_formats(
                        manifest_url, video_id, preference=preference, f4m_id=f4m_id,
                        transform_source=transform_source, fatal=fatal)
                    # Sometimes stream-level manifest contains single media entry that
                    # does not contain any quality metadata (e.g. http://matchtv.ru/#live-player).
                    # At the same time parent's media entry in set-level manifest may
                    # contain it. We will copy it from parent in such cases.
                    if len(f4m_formats) == 1:
                        f = f4m_formats[0]
                        f.update({
                            'tbr': f.get('tbr') or tbr,
                            'width': f.get('width') or width,
                            'height': f.get('height') or height,
                            'format_id': f.get('format_id') if not tbr else format_id,
                            'vcodec': vcodec,
                        })
                    formats.extend(f4m_formats)
                    continue
                elif ext == 'm3u8':
                    formats.extend(self._extract_m3u8_formats(
                        manifest_url, video_id, 'mp4', preference=preference,
                        m3u8_id=m3u8_id, fatal=fatal))
                    continue
            formats.append({
                'format_id': format_id,
                'url': manifest_url,
                'manifest_url': manifest_url,
                'ext': 'flv' if bootstrap_info is not None else None,
                'protocol': 'f4m',
                'tbr': tbr,
                'width': width,
                'height': height,
                'vcodec': vcodec,
                'preference': preference,
            })
        return formats

    def _m3u8_meta_format(self, m3u8_url, ext=None, preference=None, m3u8_id=None):
        return {
            'format_id': '-'.join(filter(None, [m3u8_id, 'meta'])),
            'url': m3u8_url,
            'ext': ext,
            'protocol': 'm3u8',
            'preference': preference - 100 if preference else -100,
            'resolution': 'multiple',
            'format_note': 'Quality selection URL',
        }

    def _extract_m3u8_formats(self, m3u8_url, video_id, ext=None,
                              entry_protocol='m3u8', preference=None,
                              m3u8_id=None, note=None, errnote=None,
                              fatal=True, live=False, data=None, headers={},
                              query={}):
        res = self._download_webpage_handle(
            m3u8_url, video_id,
            note=note or 'Downloading m3u8 information',
            errnote=errnote or 'Failed to download m3u8 information',
            fatal=fatal, data=data, headers=headers, query=query)

        if res is False:
            return []

        m3u8_doc, urlh = res
        m3u8_url = urlh.geturl()

        return self._parse_m3u8_formats(
            m3u8_doc, m3u8_url, ext=ext, entry_protocol=entry_protocol,
            preference=preference, m3u8_id=m3u8_id, live=live)

    def _parse_m3u8_formats(self, m3u8_doc, m3u8_url, ext=None,
                            entry_protocol='m3u8', preference=None,
                            m3u8_id=None, live=False):
        if '#EXT-X-FAXS-CM:' in m3u8_doc:  # Adobe Flash Access
            return []

        if re.search(r'#EXT-X-SESSION-KEY:.*?URI="skd://', m3u8_doc):  # Apple FairPlay
            return []

        formats = []

        format_url = lambda u: (
            u
            if re.match(r'^https?://', u)
            else compat_urlparse.urljoin(m3u8_url, u))

        # References:
        # 1. https://tools.ietf.org/html/draft-pantos-http-live-streaming-21
        # 2. https://github.com/ytdl-org/youtube-dl/issues/12211
        # 3. https://github.com/ytdl-org/youtube-dl/issues/18923

        # We should try extracting formats only from master playlists [1, 4.3.4],
        # i.e. playlists that describe available qualities. On the other hand
        # media playlists [1, 4.3.3] should be returned as is since they contain
        # just the media without qualities renditions.
        # Fortunately, master playlist can be easily distinguished from media
        # playlist based on particular tags availability. As of [1, 4.3.3, 4.3.4]
        # master playlist tags MUST NOT appear in a media playlist and vice versa.
        # As of [1, 4.3.3.1] #EXT-X-TARGETDURATION tag is REQUIRED for every
        # media playlist and MUST NOT appear in master playlist thus we can
        # clearly detect media playlist with this criterion.

        if '#EXT-X-TARGETDURATION' in m3u8_doc:  # media playlist, return as is
            return [{
                'url': m3u8_url,
                'format_id': m3u8_id,
                'ext': ext,
                'protocol': entry_protocol,
                'preference': preference,
            }]

        groups = {}
        last_stream_inf = {}

        def extract_media(x_media_line):
            media = parse_m3u8_attributes(x_media_line)
            # As per [1, 4.3.4.1] TYPE, GROUP-ID and NAME are REQUIRED
            media_type, group_id, name = media.get('TYPE'), media.get('GROUP-ID'), media.get('NAME')
            if not (media_type and group_id and name):
                return
            groups.setdefault(group_id, []).append(media)
            if media_type not in ('VIDEO', 'AUDIO'):
                return
            media_url = media.get('URI')
            if media_url:
                format_id = []
                for v in (m3u8_id, group_id, name):
                    if v:
                        format_id.append(v)
                f = {
                    'format_id': '-'.join(format_id),
                    'url': format_url(media_url),
                    'manifest_url': m3u8_url,
                    'language': media.get('LANGUAGE'),
                    'ext': ext,
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                if media_type == 'AUDIO':
                    f['vcodec'] = 'none'
                formats.append(f)

        def build_stream_name():
            # Despite specification does not mention NAME attribute for
            # EXT-X-STREAM-INF tag it still sometimes may be present (see [1]
            # or vidio test in TestInfoExtractor.test_parse_m3u8_formats)
            # 1. http://www.vidio.com/watch/165683-dj_ambred-booyah-live-2015
            stream_name = last_stream_inf.get('NAME')
            if stream_name:
                return stream_name
            # If there is no NAME in EXT-X-STREAM-INF it will be obtained
            # from corresponding rendition group
            stream_group_id = last_stream_inf.get('VIDEO')
            if not stream_group_id:
                return
            stream_group = groups.get(stream_group_id)
            if not stream_group:
                return stream_group_id
            rendition = stream_group[0]
            return rendition.get('NAME') or stream_group_id

        # parse EXT-X-MEDIA tags before EXT-X-STREAM-INF in order to have the
        # chance to detect video only formats when EXT-X-STREAM-INF tags
        # precede EXT-X-MEDIA tags in HLS manifest such as [3].
        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-MEDIA:'):
                extract_media(line)

        for line in m3u8_doc.splitlines():
            if line.startswith('#EXT-X-STREAM-INF:'):
                last_stream_inf = parse_m3u8_attributes(line)
            elif line.startswith('#') or not line.strip():
                continue
            else:
                tbr = float_or_none(
                    last_stream_inf.get('AVERAGE-BANDWIDTH')
                    or last_stream_inf.get('BANDWIDTH'), scale=1000)
                format_id = []
                if m3u8_id:
                    format_id.append(m3u8_id)
                stream_name = build_stream_name()
                # Bandwidth of live streams may differ over time thus making
                # format_id unpredictable. So it's better to keep provided
                # format_id intact.
                if not live:
                    format_id.append(stream_name if stream_name else '%d' % (tbr if tbr else len(formats)))
                manifest_url = format_url(line.strip())
                f = {
                    'format_id': '-'.join(format_id),
                    'url': manifest_url,
                    'manifest_url': m3u8_url,
                    'tbr': tbr,
                    'ext': ext,
                    'fps': float_or_none(last_stream_inf.get('FRAME-RATE')),
                    'protocol': entry_protocol,
                    'preference': preference,
                }
                resolution = last_stream_inf.get('RESOLUTION')
                if resolution:
                    mobj = re.search(r'(?P<width>\d+)[xX](?P<height>\d+)', resolution)
                    if mobj:
                        f['width'] = int(mobj.group('width'))
                        f['height'] = int(mobj.group('height'))
                # Unified Streaming Platform
                mobj = re.search(
                    r'audio.*?(?:%3D|=)(\d+)(?:-video.*?(?:%3D|=)(\d+))?', f['url'])
                if mobj:
                    abr, vbr = mobj.groups()
                    abr, vbr = float_or_none(abr, 1000), float_or_none(vbr, 1000)
                    f.update({
                        'vbr': vbr,
                        'abr': abr,
                    })
                codecs = parse_codecs(last_stream_inf.get('CODECS'))
                f.update(codecs)
                audio_group_id = last_stream_inf.get('AUDIO')
                # As per [1, 4.3.4.1.1] any EXT-X-STREAM-INF tag which
                # references a rendition group MUST have a CODECS attribute.
                # However, this is not always respected, for example, [2]
                # contains EXT-X-STREAM-INF tag which references AUDIO
                # rendition group but does not have CODECS and despite
                # referencing an audio group it represents a complete
                # (with audio and video) format. So, for such cases we will
                # ignore references to rendition groups and treat them
                # as complete formats.
                if audio_group_id and codecs and f.get('vcodec') != 'none':
                    audio_group = groups.get(audio_group_id)
                    if audio_group and audio_group[0].get('URI'):
                        # TODO: update acodec for audio only formats with
                        # the same GROUP-ID
                        f['acodec'] = 'none'
                formats.append(f)

                # for DailyMotion
                progressive_uri = last_stream_inf.get('PROGRESSIVE-URI')
                if progressive_uri:
                    http_f = f.copy()
                    del http_f['manifest_url']
                    http_f.update({
                        'format_id': f['format_id'].replace('hls-', 'http-'),
                        'protocol': 'http',
                        'url': progressive_uri,
                    })
                    formats.append(http_f)

                last_stream_inf = {}
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
        media = smil.findall(self._xpath_ns('.//video', namespace)) + smil.findall(self._xpath_ns('.//audio', namespace))
        for medium in media:
            src = medium.get('src')
            if not src or src in srcs:
                continue
            srcs.append(src)

            bitrate = float_or_none(medium.get('system-bitrate') or medium.get('systemBitrate'), 1000)
            filesize = int_or_none(medium.get('size') or medium.get('fileSize'))
            width = int_or_none(medium.get('width'))
            height = int_or_none(medium.get('height'))
            proto = medium.get('proto')
            ext = medium.get('ext')
            src_ext = determine_ext(src)
            streamer = medium.get('streamer') or base

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
            elif src_ext == 'f4m':
                f4m_url = src_url
                if not f4m_params:
                    f4m_params = {
                        'hdcore': '3.2.0',
                        'plugin': 'flowplayer-3.2.0.1',
                    }
                f4m_url += '&' if '?' in f4m_url else '?'
                f4m_url += compat_urllib_parse_urlencode(f4m_params)
                formats.extend(self._extract_f4m_formats(f4m_url, video_id, f4m_id='hds', fatal=False))
            elif src_ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    src_url, video_id, mpd_id='dash', fatal=False))
            elif re.search(r'\.ism/[Mm]anifest', src_url):
                formats.extend(self._extract_ism_formats(
                    src_url, video_id, ism_id='mss', fatal=False))
            elif src_url.startswith('http') and self._is_valid_url(src, video_id):
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

    def _extract_xspf_playlist(self, xspf_url, playlist_id, fatal=True):
        xspf = self._download_xml(
            xspf_url, playlist_id, 'Downloading xpsf playlist',
            'Unable to download xspf manifest', fatal=fatal)
        if xspf is False:
            return []
        return self._parse_xspf(
            xspf, playlist_id, xspf_url=xspf_url,
            xspf_base_url=base_url(xspf_url))

    def _parse_xspf(self, xspf_doc, playlist_id, xspf_url=None, xspf_base_url=None):
        NS_MAP = {
            'xspf': 'http://xspf.org/ns/0/',
            's1': 'http://static.streamone.nl/player/ns/0',
        }

        entries = []
        for track in xspf_doc.findall(xpath_with_ns('./xspf:trackList/xspf:track', NS_MAP)):
            title = xpath_text(
                track, xpath_with_ns('./xspf:title', NS_MAP), 'title', default=playlist_id)
            description = xpath_text(
                track, xpath_with_ns('./xspf:annotation', NS_MAP), 'description')
            thumbnail = xpath_text(
                track, xpath_with_ns('./xspf:image', NS_MAP), 'thumbnail')
            duration = float_or_none(
                xpath_text(track, xpath_with_ns('./xspf:duration', NS_MAP), 'duration'), 1000)

            formats = []
            for location in track.findall(xpath_with_ns('./xspf:location', NS_MAP)):
                format_url = urljoin(xspf_base_url, location.text)
                if not format_url:
                    continue
                formats.append({
                    'url': format_url,
                    'manifest_url': xspf_url,
                    'format_id': location.get(xpath_with_ns('s1:label', NS_MAP)),
                    'width': int_or_none(location.get(xpath_with_ns('s1:width', NS_MAP))),
                    'height': int_or_none(location.get(xpath_with_ns('s1:height', NS_MAP))),
                })
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

    def _extract_mpd_formats(self, mpd_url, video_id, mpd_id=None, note=None, errnote=None, fatal=True, data=None, headers={}, query={}):
        res = self._download_xml_handle(
            mpd_url, video_id,
            note=note or 'Downloading MPD manifest',
            errnote=errnote or 'Failed to download MPD manifest',
            fatal=fatal, data=data, headers=headers, query=query)
        if res is False:
            return []
        mpd_doc, urlh = res
        if mpd_doc is None:
            return []
        mpd_base_url = base_url(urlh.geturl())

        return self._parse_mpd_formats(
            mpd_doc, mpd_id, mpd_base_url, mpd_url)

    def _parse_mpd_formats(self, mpd_doc, mpd_id=None, mpd_base_url='', mpd_url=None):
        """
        Parse formats from MPD manifest.
        References:
         1. MPEG-DASH Standard, ISO/IEC 23009-1:2014(E),
            http://standards.iso.org/ittf/PubliclyAvailableStandards/c065274_ISO_IEC_23009-1_2014.zip
         2. https://en.wikipedia.org/wiki/Dynamic_Adaptive_Streaming_over_HTTP
        """
        if mpd_doc.get('type') == 'dynamic':
            return []

        namespace = self._search_regex(r'(?i)^{([^}]+)?}MPD$', mpd_doc.tag, 'namespace', default=None)

        def _add_ns(path):
            return self._xpath_ns(path, namespace)

        def is_drm_protected(element):
            return element.find(_add_ns('ContentProtection')) is not None

        def extract_multisegment_info(element, ms_parent_info):
            ms_info = ms_parent_info.copy()

            # As per [1, 5.3.9.2.2] SegmentList and SegmentTemplate share some
            # common attributes and elements.  We will only extract relevant
            # for us.
            def extract_common(source):
                segment_timeline = source.find(_add_ns('SegmentTimeline'))
                if segment_timeline is not None:
                    s_e = segment_timeline.findall(_add_ns('S'))
                    if s_e:
                        ms_info['total_number'] = 0
                        ms_info['s'] = []
                        for s in s_e:
                            r = int(s.get('r', 0))
                            ms_info['total_number'] += 1 + r
                            ms_info['s'].append({
                                't': int(s.get('t', 0)),
                                # @d is mandatory (see [1, 5.3.9.6.2, Table 17, page 60])
                                'd': int(s.attrib['d']),
                                'r': r,
                            })
                start_number = source.get('startNumber')
                if start_number:
                    ms_info['start_number'] = int(start_number)
                timescale = source.get('timescale')
                if timescale:
                    ms_info['timescale'] = int(timescale)
                segment_duration = source.get('duration')
                if segment_duration:
                    ms_info['segment_duration'] = float(segment_duration)

            def extract_Initialization(source):
                initialization = source.find(_add_ns('Initialization'))
                if initialization is not None:
                    ms_info['initialization_url'] = initialization.attrib['sourceURL']

            segment_list = element.find(_add_ns('SegmentList'))
            if segment_list is not None:
                extract_common(segment_list)
                extract_Initialization(segment_list)
                segment_urls_e = segment_list.findall(_add_ns('SegmentURL'))
                if segment_urls_e:
                    ms_info['segment_urls'] = [segment.attrib['media'] for segment in segment_urls_e]
            else:
                segment_template = element.find(_add_ns('SegmentTemplate'))
                if segment_template is not None:
                    extract_common(segment_template)
                    media = segment_template.get('media')
                    if media:
                        ms_info['media'] = media
                    initialization = segment_template.get('initialization')
                    if initialization:
                        ms_info['initialization'] = initialization
                    else:
                        extract_Initialization(segment_template)
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
                    # According to [1, 5.3.7.2, Table 9, page 41], @mimeType is mandatory
                    mime_type = representation_attrib['mimeType']
                    content_type = mime_type.split('/')[0]
                    if content_type == 'text':
                        # TODO implement WebVTT downloading
                        pass
                    elif content_type in ('video', 'audio'):
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
                        bandwidth = int_or_none(representation_attrib.get('bandwidth'))
                        f = {
                            'format_id': '%s-%s' % (mpd_id, representation_id) if mpd_id else representation_id,
                            'manifest_url': mpd_url,
                            'ext': mimetype2ext(mime_type),
                            'width': int_or_none(representation_attrib.get('width')),
                            'height': int_or_none(representation_attrib.get('height')),
                            'tbr': float_or_none(bandwidth, 1000),
                            'asr': int_or_none(representation_attrib.get('audioSamplingRate')),
                            'fps': int_or_none(representation_attrib.get('frameRate')),
                            'language': lang if lang not in ('mul', 'und', 'zxx', 'mis') else None,
                            'format_note': 'DASH %s' % content_type,
                            'filesize': filesize,
                            'container': mimetype2ext(mime_type) + '_dash',
                        }
                        f.update(parse_codecs(representation_attrib.get('codecs')))
                        representation_ms_info = extract_multisegment_info(representation, adaption_set_ms_info)

                        def prepare_template(template_name, identifiers):
                            tmpl = representation_ms_info[template_name]
                            # First of, % characters outside $...$ templates
                            # must be escaped by doubling for proper processing
                            # by % operator string formatting used further (see
                            # https://github.com/ytdl-org/youtube-dl/issues/16867).
                            t = ''
                            in_template = False
                            for c in tmpl:
                                t += c
                                if c == '$':
                                    in_template = not in_template
                                elif c == '%' and not in_template:
                                    t += c
                            # Next, $...$ templates are translated to their
                            # %(...) counterparts to be used with % operator
                            t = t.replace('$RepresentationID$', representation_id)
                            t = re.sub(r'\$(%s)\$' % '|'.join(identifiers), r'%(\1)d', t)
                            t = re.sub(r'\$(%s)%%([^$]+)\$' % '|'.join(identifiers), r'%(\1)\2', t)
                            t.replace('$$', '$')
                            return t

                        # @initialization is a regular template like @media one
                        # so it should be handled just the same way (see
                        # https://github.com/ytdl-org/youtube-dl/issues/11605)
                        if 'initialization' in representation_ms_info:
                            initialization_template = prepare_template(
                                'initialization',
                                # As per [1, 5.3.9.4.2, Table 15, page 54] $Number$ and
                                # $Time$ shall not be included for @initialization thus
                                # only $Bandwidth$ remains
                                ('Bandwidth', ))
                            representation_ms_info['initialization_url'] = initialization_template % {
                                'Bandwidth': bandwidth,
                            }

                        def location_key(location):
                            return 'url' if re.match(r'^https?://', location) else 'path'

                        if 'segment_urls' not in representation_ms_info and 'media' in representation_ms_info:

                            media_template = prepare_template('media', ('Number', 'Bandwidth', 'Time'))
                            media_location_key = location_key(media_template)

                            # As per [1, 5.3.9.4.4, Table 16, page 55] $Number$ and $Time$
                            # can't be used at the same time
                            if '%(Number' in media_template and 's' not in representation_ms_info:
                                segment_duration = None
                                if 'total_number' not in representation_ms_info and 'segment_duration' in representation_ms_info:
                                    segment_duration = float_or_none(representation_ms_info['segment_duration'], representation_ms_info['timescale'])
                                    representation_ms_info['total_number'] = int(math.ceil(float(period_duration) / segment_duration))
                                representation_ms_info['fragments'] = [{
                                    media_location_key: media_template % {
                                        'Number': segment_number,
                                        'Bandwidth': bandwidth,
                                    },
                                    'duration': segment_duration,
                                } for segment_number in range(
                                    representation_ms_info['start_number'],
                                    representation_ms_info['total_number'] + representation_ms_info['start_number'])]
                            else:
                                # $Number*$ or $Time$ in media template with S list available
                                # Example $Number*$: http://www.svtplay.se/klipp/9023742/stopptid-om-bjorn-borg
                                # Example $Time$: https://play.arkena.com/embed/avp/v2/player/media/b41dda37-d8e7-4d3f-b1b5-9a9db578bdfe/1/129411
                                representation_ms_info['fragments'] = []
                                segment_time = 0
                                segment_d = None
                                segment_number = representation_ms_info['start_number']

                                def add_segment_url():
                                    segment_url = media_template % {
                                        'Time': segment_time,
                                        'Bandwidth': bandwidth,
                                        'Number': segment_number,
                                    }
                                    representation_ms_info['fragments'].append({
                                        media_location_key: segment_url,
                                        'duration': float_or_none(segment_d, representation_ms_info['timescale']),
                                    })

                                for num, s in enumerate(representation_ms_info['s']):
                                    segment_time = s.get('t') or segment_time
                                    segment_d = s['d']
                                    add_segment_url()
                                    segment_number += 1
                                    for r in range(s.get('r', 0)):
                                        segment_time += segment_d
                                        add_segment_url()
                                        segment_number += 1
                                    segment_time += segment_d
                        elif 'segment_urls' in representation_ms_info and 's' in representation_ms_info:
                            # No media template
                            # Example: https://www.youtube.com/watch?v=iXZV5uAYMJI
                            # or any YouTube dashsegments video
                            fragments = []
                            segment_index = 0
                            timescale = representation_ms_info['timescale']
                            for s in representation_ms_info['s']:
                                duration = float_or_none(s['d'], timescale)
                                for r in range(s.get('r', 0) + 1):
                                    segment_uri = representation_ms_info['segment_urls'][segment_index]
                                    fragments.append({
                                        location_key(segment_uri): segment_uri,
                                        'duration': duration,
                                    })
                                    segment_index += 1
                            representation_ms_info['fragments'] = fragments
                        elif 'segment_urls' in representation_ms_info:
                            # Segment URLs with no SegmentTimeline
                            # Example: https://www.seznam.cz/zpravy/clanek/cesko-zasahne-vitr-o-sile-vichrice-muze-byt-i-zivotu-nebezpecny-39091
                            # https://github.com/ytdl-org/youtube-dl/pull/14844
                            fragments = []
                            segment_duration = float_or_none(
                                representation_ms_info['segment_duration'],
                                representation_ms_info['timescale']) if 'segment_duration' in representation_ms_info else None
                            for segment_url in representation_ms_info['segment_urls']:
                                fragment = {
                                    location_key(segment_url): segment_url,
                                }
                                if segment_duration:
                                    fragment['duration'] = segment_duration
                                fragments.append(fragment)
                            representation_ms_info['fragments'] = fragments
                        # If there is a fragments key available then we correctly recognized fragmented media.
                        # Otherwise we will assume unfragmented media with direct access. Technically, such
                        # assumption is not necessarily correct since we may simply have no support for
                        # some forms of fragmented media renditions yet, but for now we'll use this fallback.
                        if 'fragments' in representation_ms_info:
                            f.update({
                                # NB: mpd_url may be empty when MPD manifest is parsed from a string
                                'url': mpd_url or base_url,
                                'fragment_base_url': base_url,
                                'fragments': [],
                                'protocol': 'http_dash_segments',
                            })
                            if 'initialization_url' in representation_ms_info:
                                initialization_url = representation_ms_info['initialization_url']
                                if not f.get('url'):
                                    f['url'] = initialization_url
                                f['fragments'].append({location_key(initialization_url): initialization_url})
                            f['fragments'].extend(representation_ms_info['fragments'])
                        else:
                            # Assuming direct URL to unfragmented media.
                            f['url'] = base_url
                        formats.append(f)
                    else:
                        self.report_warning('Unknown MIME type %s in DASH manifest' % mime_type)
        return formats

    def _extract_ism_formats(self, ism_url, video_id, ism_id=None, note=None, errnote=None, fatal=True, data=None, headers={}, query={}):
        res = self._download_xml_handle(
            ism_url, video_id,
            note=note or 'Downloading ISM manifest',
            errnote=errnote or 'Failed to download ISM manifest',
            fatal=fatal, data=data, headers=headers, query=query)
        if res is False:
            return []
        ism_doc, urlh = res
        if ism_doc is None:
            return []

        return self._parse_ism_formats(ism_doc, urlh.geturl(), ism_id)

    def _parse_ism_formats(self, ism_doc, ism_url, ism_id=None):
        """
        Parse formats from ISM manifest.
        References:
         1. [MS-SSTR]: Smooth Streaming Protocol,
            https://msdn.microsoft.com/en-us/library/ff469518.aspx
        """
        if ism_doc.get('IsLive') == 'TRUE' or ism_doc.find('Protection') is not None:
            return []

        duration = int(ism_doc.attrib['Duration'])
        timescale = int_or_none(ism_doc.get('TimeScale')) or 10000000

        formats = []
        for stream in ism_doc.findall('StreamIndex'):
            stream_type = stream.get('Type')
            if stream_type not in ('video', 'audio'):
                continue
            url_pattern = stream.attrib['Url']
            stream_timescale = int_or_none(stream.get('TimeScale')) or timescale
            stream_name = stream.get('Name')
            for track in stream.findall('QualityLevel'):
                fourcc = track.get('FourCC', 'AACL' if track.get('AudioTag') == '255' else None)
                # TODO: add support for WVC1 and WMAP
                if fourcc not in ('H264', 'AVC1', 'AACL'):
                    self.report_warning('%s is not a supported codec' % fourcc)
                    continue
                tbr = int(track.attrib['Bitrate']) // 1000
                # [1] does not mention Width and Height attributes. However,
                # they're often present while MaxWidth and MaxHeight are
                # missing, so should be used as fallbacks
                width = int_or_none(track.get('MaxWidth') or track.get('Width'))
                height = int_or_none(track.get('MaxHeight') or track.get('Height'))
                sampling_rate = int_or_none(track.get('SamplingRate'))

                track_url_pattern = re.sub(r'{[Bb]itrate}', track.attrib['Bitrate'], url_pattern)
                track_url_pattern = compat_urlparse.urljoin(ism_url, track_url_pattern)

                fragments = []
                fragment_ctx = {
                    'time': 0,
                }
                stream_fragments = stream.findall('c')
                for stream_fragment_index, stream_fragment in enumerate(stream_fragments):
                    fragment_ctx['time'] = int_or_none(stream_fragment.get('t')) or fragment_ctx['time']
                    fragment_repeat = int_or_none(stream_fragment.get('r')) or 1
                    fragment_ctx['duration'] = int_or_none(stream_fragment.get('d'))
                    if not fragment_ctx['duration']:
                        try:
                            next_fragment_time = int(stream_fragment[stream_fragment_index + 1].attrib['t'])
                        except IndexError:
                            next_fragment_time = duration
                        fragment_ctx['duration'] = (next_fragment_time - fragment_ctx['time']) / fragment_repeat
                    for _ in range(fragment_repeat):
                        fragments.append({
                            'url': re.sub(r'{start[ _]time}', compat_str(fragment_ctx['time']), track_url_pattern),
                            'duration': fragment_ctx['duration'] / stream_timescale,
                        })
                        fragment_ctx['time'] += fragment_ctx['duration']

                format_id = []
                if ism_id:
                    format_id.append(ism_id)
                if stream_name:
                    format_id.append(stream_name)
                format_id.append(compat_str(tbr))

                formats.append({
                    'format_id': '-'.join(format_id),
                    'url': ism_url,
                    'manifest_url': ism_url,
                    'ext': 'ismv' if stream_type == 'video' else 'isma',
                    'width': width,
                    'height': height,
                    'tbr': tbr,
                    'asr': sampling_rate,
                    'vcodec': 'none' if stream_type == 'audio' else fourcc,
                    'acodec': 'none' if stream_type == 'video' else fourcc,
                    'protocol': 'ism',
                    'fragments': fragments,
                    '_download_params': {
                        'duration': duration,
                        'timescale': stream_timescale,
                        'width': width or 0,
                        'height': height or 0,
                        'fourcc': fourcc,
                        'codec_private_data': track.get('CodecPrivateData'),
                        'sampling_rate': sampling_rate,
                        'channels': int_or_none(track.get('Channels', 2)),
                        'bits_per_sample': int_or_none(track.get('BitsPerSample', 16)),
                        'nal_unit_length_field': int_or_none(track.get('NALUnitLengthField', 4)),
                    },
                })
        return formats

    def _parse_html5_media_entries(self, base_url, webpage, video_id, m3u8_id=None, m3u8_entry_protocol='m3u8', mpd_id=None, preference=None):
        def absolute_url(item_url):
            return urljoin(base_url, item_url)

        def parse_content_type(content_type):
            if not content_type:
                return {}
            ctr = re.search(r'(?P<mimetype>[^/]+/[^;]+)(?:;\s*codecs="?(?P<codecs>[^"]+))?', content_type)
            if ctr:
                mimetype, codecs = ctr.groups()
                f = parse_codecs(codecs)
                f['ext'] = mimetype2ext(mimetype)
                return f
            return {}

        def _media_formats(src, cur_media_type, type_info={}):
            full_url = absolute_url(src)
            ext = type_info.get('ext') or determine_ext(full_url)
            if ext == 'm3u8':
                is_plain_url = False
                formats = self._extract_m3u8_formats(
                    full_url, video_id, ext='mp4',
                    entry_protocol=m3u8_entry_protocol, m3u8_id=m3u8_id,
                    preference=preference, fatal=False)
            elif ext == 'mpd':
                is_plain_url = False
                formats = self._extract_mpd_formats(
                    full_url, video_id, mpd_id=mpd_id, fatal=False)
            else:
                is_plain_url = True
                formats = [{
                    'url': full_url,
                    'vcodec': 'none' if cur_media_type == 'audio' else None,
                }]
            return is_plain_url, formats

        entries = []
        # amp-video and amp-audio are very similar to their HTML5 counterparts
        # so we wll include them right here (see
        # https://www.ampproject.org/docs/reference/components/amp-video)
        # For dl8-* tags see https://delight-vr.com/documentation/dl8-video/
        _MEDIA_TAG_NAME_RE = r'(?:(?:amp|dl8(?:-live)?)-)?(video|audio)'
        media_tags = [(media_tag, media_tag_name, media_type, '')
                      for media_tag, media_tag_name, media_type
                      in re.findall(r'(?s)(<(%s)[^>]*/>)' % _MEDIA_TAG_NAME_RE, webpage)]
        media_tags.extend(re.findall(
            # We only allow video|audio followed by a whitespace or '>'.
            # Allowing more characters may end up in significant slow down (see
            # https://github.com/ytdl-org/youtube-dl/issues/11979, example URL:
            # http://www.porntrex.com/maps/videositemap.xml).
            r'(?s)(<(?P<tag>%s)(?:\s+[^>]*)?>)(.*?)</(?P=tag)>' % _MEDIA_TAG_NAME_RE, webpage))
        for media_tag, _, media_type, media_content in media_tags:
            media_info = {
                'formats': [],
                'subtitles': {},
            }
            media_attributes = extract_attributes(media_tag)
            src = strip_or_none(media_attributes.get('src'))
            if src:
                _, formats = _media_formats(src, media_type)
                media_info['formats'].extend(formats)
            media_info['thumbnail'] = absolute_url(media_attributes.get('poster'))
            if media_content:
                for source_tag in re.findall(r'<source[^>]+>', media_content):
                    s_attr = extract_attributes(source_tag)
                    # data-video-src and data-src are non standard but seen
                    # several times in the wild
                    src = strip_or_none(dict_get(s_attr, ('src', 'data-video-src', 'data-src')))
                    if not src:
                        continue
                    f = parse_content_type(s_attr.get('type'))
                    is_plain_url, formats = _media_formats(src, media_type, f)
                    if is_plain_url:
                        # width, height, res, label and title attributes are
                        # all not standard but seen several times in the wild
                        labels = [
                            s_attr.get(lbl)
                            for lbl in ('label', 'title')
                            if str_or_none(s_attr.get(lbl))
                        ]
                        width = int_or_none(s_attr.get('width'))
                        height = (int_or_none(s_attr.get('height'))
                                  or int_or_none(s_attr.get('res')))
                        if not width or not height:
                            for lbl in labels:
                                resolution = parse_resolution(lbl)
                                if not resolution:
                                    continue
                                width = width or resolution.get('width')
                                height = height or resolution.get('height')
                        for lbl in labels:
                            tbr = parse_bitrate(lbl)
                            if tbr:
                                break
                        else:
                            tbr = None
                        f.update({
                            'width': width,
                            'height': height,
                            'tbr': tbr,
                            'format_id': s_attr.get('label') or s_attr.get('title'),
                        })
                        f.update(formats[0])
                        media_info['formats'].append(f)
                    else:
                        media_info['formats'].extend(formats)
                for track_tag in re.findall(r'<track[^>]+>', media_content):
                    track_attributes = extract_attributes(track_tag)
                    kind = track_attributes.get('kind')
                    if not kind or kind in ('subtitles', 'captions'):
                        src = strip_or_none(track_attributes.get('src'))
                        if not src:
                            continue
                        lang = track_attributes.get('srclang') or track_attributes.get('lang') or track_attributes.get('label')
                        media_info['subtitles'].setdefault(lang, []).append({
                            'url': absolute_url(src),
                        })
            for f in media_info['formats']:
                f.setdefault('http_headers', {})['Referer'] = base_url
            if media_info['formats'] or media_info['subtitles']:
                entries.append(media_info)
        return entries

    def _extract_akamai_formats(self, manifest_url, video_id, hosts={}):
        signed = 'hdnea=' in manifest_url
        if not signed:
            # https://learn.akamai.com/en-us/webhelp/media-services-on-demand/stream-packaging-user-guide/GUID-BE6C0F73-1E06-483B-B0EA-57984B91B7F9.html
            manifest_url = re.sub(
                r'(?:b=[\d,-]+|(?:__a__|attributes)=off|__b__=\d+)&?',
                '', manifest_url).strip('?')

        formats = []

        hdcore_sign = 'hdcore=3.7.0'
        f4m_url = re.sub(r'(https?://[^/]+)/i/', r'\1/z/', manifest_url).replace('/master.m3u8', '/manifest.f4m')
        hds_host = hosts.get('hds')
        if hds_host:
            f4m_url = re.sub(r'(https?://)[^/]+', r'\1' + hds_host, f4m_url)
        if 'hdcore=' not in f4m_url:
            f4m_url += ('&' if '?' in f4m_url else '?') + hdcore_sign
        f4m_formats = self._extract_f4m_formats(
            f4m_url, video_id, f4m_id='hds', fatal=False)
        for entry in f4m_formats:
            entry.update({'extra_param_to_segment_url': hdcore_sign})
        formats.extend(f4m_formats)

        m3u8_url = re.sub(r'(https?://[^/]+)/z/', r'\1/i/', manifest_url).replace('/manifest.f4m', '/master.m3u8')
        hls_host = hosts.get('hls')
        if hls_host:
            m3u8_url = re.sub(r'(https?://)[^/]+', r'\1' + hls_host, m3u8_url)
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls', fatal=False)
        formats.extend(m3u8_formats)

        http_host = hosts.get('http')
        if http_host and m3u8_formats and not signed:
            REPL_REGEX = r'https?://[^/]+/i/([^,]+),([^/]+),([^/]+)\.csmil/.+'
            qualities = re.match(REPL_REGEX, m3u8_url).group(2).split(',')
            qualities_length = len(qualities)
            if len(m3u8_formats) in (qualities_length, qualities_length + 1):
                i = 0
                for f in m3u8_formats:
                    if f['vcodec'] != 'none':
                        for protocol in ('http', 'https'):
                            http_f = f.copy()
                            del http_f['manifest_url']
                            http_url = re.sub(
                                REPL_REGEX, protocol + r'://%s/\g<1>%s\3' % (http_host, qualities[i]), f['url'])
                            http_f.update({
                                'format_id': http_f['format_id'].replace('hls-', protocol + '-'),
                                'url': http_url,
                                'protocol': protocol,
                            })
                            formats.append(http_f)
                        i += 1

        return formats

    def _extract_wowza_formats(self, url, video_id, m3u8_entry_protocol='m3u8_native', skip_protocols=[]):
        query = compat_urlparse.urlparse(url).query
        url = re.sub(r'/(?:manifest|playlist|jwplayer)\.(?:m3u8|f4m|mpd|smil)', '', url)
        mobj = re.search(
            r'(?:(?:http|rtmp|rtsp)(?P<s>s)?:)?(?P<url>//[^?]+)', url)
        url_base = mobj.group('url')
        http_base_url = '%s%s:%s' % ('http', mobj.group('s') or '', url_base)
        formats = []

        def manifest_url(manifest):
            m_url = '%s/%s' % (http_base_url, manifest)
            if query:
                m_url += '?%s' % query
            return m_url

        if 'm3u8' not in skip_protocols:
            formats.extend(self._extract_m3u8_formats(
                manifest_url('playlist.m3u8'), video_id, 'mp4',
                m3u8_entry_protocol, m3u8_id='hls', fatal=False))
        if 'f4m' not in skip_protocols:
            formats.extend(self._extract_f4m_formats(
                manifest_url('manifest.f4m'),
                video_id, f4m_id='hds', fatal=False))
        if 'dash' not in skip_protocols:
            formats.extend(self._extract_mpd_formats(
                manifest_url('manifest.mpd'),
                video_id, mpd_id='dash', fatal=False))
        if re.search(r'(?:/smil:|\.smil)', url_base):
            if 'smil' not in skip_protocols:
                rtmp_formats = self._extract_smil_formats(
                    manifest_url('jwplayer.smil'),
                    video_id, fatal=False)
                for rtmp_format in rtmp_formats:
                    rtsp_format = rtmp_format.copy()
                    rtsp_format['url'] = '%s/%s' % (rtmp_format['url'], rtmp_format['play_path'])
                    del rtsp_format['play_path']
                    del rtsp_format['ext']
                    rtsp_format.update({
                        'url': rtsp_format['url'].replace('rtmp://', 'rtsp://'),
                        'format_id': rtmp_format['format_id'].replace('rtmp', 'rtsp'),
                        'protocol': 'rtsp',
                    })
                    formats.extend([rtmp_format, rtsp_format])
        else:
            for protocol in ('rtmp', 'rtsp'):
                if protocol not in skip_protocols:
                    formats.append({
                        'url': '%s:%s' % (protocol, url_base),
                        'format_id': protocol,
                        'protocol': protocol,
                    })
        return formats

    def _find_jwplayer_data(self, webpage, video_id=None, transform_source=js_to_json):
        mobj = re.search(
            r'''(?s)jwplayer\s*\(\s*(?P<q>'|")(?!(?P=q)).+(?P=q)\s*\)(?!</script>).*?\.\s*setup\s*\(\s*(?P<options>(?:\([^)]*\)|[^)])+)\s*\)''',
            webpage)
        if mobj:
            try:
                jwplayer_data = self._parse_json(mobj.group('options'),
                                                 video_id=video_id,
                                                 transform_source=transform_source)
            except ExtractorError:
                pass
            else:
                if isinstance(jwplayer_data, dict):
                    return jwplayer_data

    def _extract_jwplayer_data(self, webpage, video_id, *args, **kwargs):
        jwplayer_data = self._find_jwplayer_data(
            webpage, video_id, transform_source=js_to_json)
        return self._parse_jwplayer_data(
            jwplayer_data, video_id, *args, **kwargs)

    def _parse_jwplayer_data(self, jwplayer_data, video_id=None, require_title=True,
                             m3u8_id=None, mpd_id=None, rtmp_params=None, base_url=None):
        flat_pl = try_get(jwplayer_data, lambda x: x.get('playlist') or True)
        if flat_pl is None:
            # not even a dict
            return []

        # JWPlayer backward compatibility: flattened playlists
        # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/api/config.js#L81-L96
        if flat_pl is True:
            jwplayer_data = {'playlist': [jwplayer_data]}

        entries = []

        # JWPlayer backward compatibility: single playlist item
        # https://github.com/jwplayer/jwplayer/blob/v7.7.0/src/js/playlist/playlist.js#L10
        if not isinstance(jwplayer_data['playlist'], list):
            jwplayer_data['playlist'] = [jwplayer_data['playlist']]

        for video_data in jwplayer_data['playlist']:
            # JWPlayer backward compatibility: flattened sources
            # https://github.com/jwplayer/jwplayer/blob/v7.4.3/src/js/playlist/item.js#L29-L35
            if 'sources' not in video_data:
                video_data['sources'] = [video_data]

            this_video_id = video_id or video_data['mediaid']

            formats = self._parse_jwplayer_formats(
                video_data['sources'], video_id=this_video_id, m3u8_id=m3u8_id,
                mpd_id=mpd_id, rtmp_params=rtmp_params, base_url=base_url)

            subtitles = {}
            tracks = video_data.get('tracks')
            if tracks and isinstance(tracks, list):
                for track in tracks:
                    if not isinstance(track, dict):
                        continue
                    track_kind = track.get('kind')
                    if not track_kind or not isinstance(track_kind, compat_str):
                        continue
                    if track_kind.lower() not in ('captions', 'subtitles'):
                        continue
                    track_url = urljoin(base_url, track.get('file'))
                    if not track_url:
                        continue
                    subtitles.setdefault(track.get('label') or 'en', []).append({
                        'url': self._proto_relative_url(track_url)
                    })

            entry = {
                'id': this_video_id,
                'title': unescapeHTML(video_data['title'] if require_title else video_data.get('title')),
                'description': clean_html(video_data.get('description')),
                'thumbnail': urljoin(base_url, self._proto_relative_url(video_data.get('image'))),
                'timestamp': int_or_none(video_data.get('pubdate')),
                'duration': float_or_none(jwplayer_data.get('duration') or video_data.get('duration')),
                'subtitles': subtitles,
                'alt_title': clean_html(video_data.get('subtitle')),  # attributes used e.g. by Tele5 ...
                'genre': clean_html(video_data.get('genre')),
                'channel': clean_html(dict_get(video_data, ('category', 'channel'))),
                'season_number': int_or_none(video_data.get('season')),
                'episode_number': int_or_none(video_data.get('episode')),
                'release_year': int_or_none(video_data.get('releasedate')),
                'age_limit': int_or_none(video_data.get('age_restriction')),
            }
            # https://github.com/jwplayer/jwplayer/blob/master/src/js/utils/validator.js#L32
            if len(formats) == 1 and re.search(r'^(?:http|//).*(?:youtube\.com|youtu\.be)/.+', formats[0]['url']):
                entry.update({
                    '_type': 'url_transparent',
                    'url': formats[0]['url'],
                })
            else:
                # avoid exception in case of only sttls
                if formats:
                    self._sort_formats(formats)
                entry['formats'] = formats
            entries.append(entry)
        if len(entries) == 1:
            return entries[0]
        else:
            return self.playlist_result(entries)

    def _parse_jwplayer_formats(self, jwplayer_sources_data, video_id=None,
                                m3u8_id=None, mpd_id=None, rtmp_params=None, base_url=None):
        urls = set()
        formats = []
        for source in jwplayer_sources_data:
            if not isinstance(source, dict):
                continue
            source_url = urljoin(
                base_url, self._proto_relative_url(source.get('file')))
            if not source_url or source_url in urls:
                continue
            urls.add(source_url)
            source_type = source.get('type') or ''
            ext = mimetype2ext(source_type) or determine_ext(source_url)
            if source_type == 'hls' or ext == 'm3u8' or 'format=m3u8-aapl' in source_url:
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=m3u8_id, fatal=False))
            elif source_type == 'dash' or ext == 'mpd' or 'format=mpd-time-csf' in source_url:
                formats.extend(self._extract_mpd_formats(
                    source_url, video_id, mpd_id=mpd_id, fatal=False))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    source_url, video_id, fatal=False))
            # https://github.com/jwplayer/jwplayer/blob/master/src/js/providers/default.js#L67
            elif source_type.startswith('audio') or ext in (
                    'oga', 'aac', 'mp3', 'mpeg', 'vorbis'):
                formats.append({
                    'url': source_url,
                    'vcodec': 'none',
                    'ext': ext,
                })
            else:
                format_id = str_or_none(source.get('label'))
                height = int_or_none(source.get('height'))
                if height is None and format_id:
                    # Often no height is provided but there is a label in
                    # format like "1080p", "720p SD", or 1080.
                    height = parse_resolution(format_id).get('height')
                a_format = {
                    'url': source_url,
                    'width': int_or_none(source.get('width')),
                    'height': height,
                    'tbr': int_or_none(source.get('bitrate'), scale=1000),
                    'filesize': int_or_none(source.get('filesize')),
                    'ext': ext,
                }
                if format_id:
                    a_format['format_id'] = format_id

                if source_url.startswith('rtmp'):
                    a_format['ext'] = 'flv'
                    # See com/longtailvideo/jwplayer/media/RTMPMediaProvider.as
                    # of jwplayer.flash.swf
                    rtmp_url_parts = re.split(
                        r'((?:mp4|mp3|flv):)', source_url, 1)
                    if len(rtmp_url_parts) == 3:
                        rtmp_url, prefix, play_path = rtmp_url_parts
                        a_format.update({
                            'url': rtmp_url,
                            'play_path': prefix + play_path,
                        })
                    if rtmp_params:
                        a_format.update(rtmp_params)
                formats.append(a_format)
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

    def _set_cookie(self, domain, name, value, expire_time=None, port=None,
                    path='/', secure=False, discard=False, rest={}, **kwargs):
        cookie = compat_cookiejar_Cookie(
            0, name, value, port, port is not None, domain, True,
            domain.startswith('.'), path, True, secure, expire_time,
            discard, None, None, rest)
        self._downloader.cookiejar.set_cookie(cookie)

    def _get_cookies(self, url):
        """ Return a compat_cookies_SimpleCookie with the cookies for the url """
        req = sanitized_Request(url)
        self._downloader.cookiejar.add_cookie_header(req)
        return compat_cookies_SimpleCookie(req.get_header('Cookie'))

    def _apply_first_set_cookie_header(self, url_handle, cookie):
        """
        Apply first Set-Cookie header instead of the last. Experimental.

        Some sites (e.g. [1-3]) may serve two cookies under the same name
        in Set-Cookie header and expect the first (old) one to be set rather
        than second (new). However, as of RFC6265 the newer one cookie
        should be set into cookie store what actually happens.
        We will workaround this issue by resetting the cookie to
        the first one manually.
        1. https://new.vk.com/
        2. https://github.com/ytdl-org/youtube-dl/issues/9841#issuecomment-227871201
        3. https://learning.oreilly.com/
        """
        for header, cookies in url_handle.headers.items():
            if header.lower() != 'set-cookie':
                continue
            if sys.version_info[0] >= 3:
                cookies = cookies.encode('iso-8859-1')
            cookies = cookies.decode('utf-8')
            cookie_value = re.search(
                r'%s=(.+?);.*?\b[Dd]omain=(.+?)(?:[,;]|$)' % cookie, cookies)
            if cookie_value:
                value, domain = cookie_value.groups()
                self._set_cookie(domain, cookie, value)
                break

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
            if tc.get('playlist', []):
                tc = tc['playlist'][0]
            is_restricted = age_restricted(
                tc.get('info_dict', {}).get('age_limit'), age_limit)
            if not is_restricted:
                return True
            any_restricted = any_restricted or is_restricted
        return not any_restricted

    def extract_subtitles(self, *args, **kwargs):
        if (self._downloader.params.get('writesubtitles', False)
                or self._downloader.params.get('listsubtitles')):
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
        if (self._downloader.params.get('writeautomaticsub', False)
                or self._downloader.params.get('listsubtitles')):
            return self._get_automatic_captions(*args, **kwargs)
        return {}

    def _get_automatic_captions(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented by subclasses')

    def mark_watched(self, *args, **kwargs):
        if (self._downloader.params.get('mark_watched', False)
                and (self._get_login_info()[0] is not None
                     or self._downloader.params.get('cookiefile') is not None)):
            self._mark_watched(*args, **kwargs)

    def _mark_watched(self, *args, **kwargs):
        raise NotImplementedError('This method must be implemented by subclasses')

    def geo_verification_headers(self):
        headers = {}
        geo_verification_proxy = self._downloader.params.get('geo_verification_proxy')
        if geo_verification_proxy:
            headers['Ytdl-request-proxy'] = geo_verification_proxy
        return headers

    def _generic_id(self, url):
        return compat_urllib_parse_unquote(os.path.splitext(url.rstrip('/').split('/')[-1])[0])

    def _generic_title(self, url):
        return compat_urllib_parse_unquote(os.path.splitext(url_basename(url))[0])


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
